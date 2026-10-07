# PostgreSQL Database Schema

## 1. Назначение

PostgreSQL является основным хранилищем данных проекта `monitoring-rsvn`.

База данных хранит:

* список камер;
* параметры камер;
* учётные данные, необходимые для SNMP/RTSP/WINK;
* результаты SNMP-опросов;
* подключённых к камере RTSP-клиентов;
* результаты WINK/RTSP-тестов;
* обнаруженные RTSP-потоки;
* историю измерений.

JSON-файлы больше не являются основным хранилищем результатов мониторинга.

---

# 2. Общая модель

```text
cameras
   │
   ├── camera_credentials
   │
   ├── snmp_measurements
   │       │
   │       └── rtsp_clients
   │
   └── wink_measurements
           │
           └── wink_streams
```

Одна камера может иметь:

* множество SNMP измерений;
* множество WINK измерений;
* множество подключённых RTSP клиентов в каждом SNMP измерении;
* множество потоков в каждом WINK измерении.

Таким образом сохраняется история мониторинга, а не только последнее состояние камеры.

---

# 3. Таблица `cameras`

Основная таблица оборудования.

| Поле            | Тип PostgreSQL | NULL | Описание                          |
| --------------- | -------------- | ---: | --------------------------------- |
| `id`            | BIGSERIAL      |   NO | Внутренний идентификатор          |
| `camera_number` | INTEGER        |   NO | Номер камеры / ТЗ                 |
| `name`          | VARCHAR(255)   |  YES | Человекочитаемое название         |
| `ip_address`    | INET           |   NO | IP-адрес камеры                   |
| `manufacturer`  | VARCHAR(255)   |  YES | Производитель                     |
| `model`         | VARCHAR(255)   |  YES | Модель камеры                     |
| `operator`      | VARCHAR(255)   |  YES | Оператор                          |
| `order_number`  | VARCHAR(100)   |  YES | Номер заказа                      |
| `rtsp_url`      | TEXT           |   NO | RTSP URL                          |
| `enabled`       | BOOLEAN        |   NO | Участвует ли камера в мониторинге |
| `created_at`    | TIMESTAMPTZ    |   NO | Дата создания                     |
| `updated_at`    | TIMESTAMPTZ    |   NO | Дата изменения                    |

### Ограничения

```text
PRIMARY KEY (id)
UNIQUE (camera_number)
```

`ip_address` индексируется.

`enabled` индексируется для быстрого получения списка активных камер.

---

# 4. Таблица `camera_credentials`

Учётные данные камеры.

Пароли НЕ удаляются из проекта.

Они должны оставаться доступными системе для выполнения SNMP/RTSP/WINK операций.

| Поле             | Тип PostgreSQL | NULL | Описание          |
| ---------------- | -------------- | ---: | ----------------- |
| `id`             | BIGSERIAL      |   NO | Идентификатор     |
| `camera_id`      | BIGINT         |   NO | FK → cameras.id   |
| `username`       | VARCHAR(255)   |  YES | Пользователь RTSP |
| `password`       | TEXT           |  YES | Пароль            |
| `snmp_community` | TEXT           |  YES | SNMP community    |
| `created_at`     | TIMESTAMPTZ    |   NO | Дата создания     |
| `updated_at`     | TIMESTAMPTZ    |   NO | Дата изменения    |

### Ограничения

```text
PRIMARY KEY (id)
FOREIGN KEY (camera_id) REFERENCES cameras(id)
UNIQUE (camera_id)
```

На данном этапе пароль хранится в БД в рабочем виде, поскольку существующий WINK workflow использует его непосредственно.

Пароли:

* не выводятся в обычные логи;
* не отображаются в Dashboard;
* не включаются в диагностические сообщения;
* не используются как обычные поля поиска.

Шифрование паролей при хранении является отдельной задачей безопасности и не должно ломать текущую функциональность мониторинга.

---

# 5. Таблица `snmp_measurements`

Одно измерение = один законченный SNMP-опрос одной камеры.

| Поле                         | Тип PostgreSQL | NULL | Описание                                |
| ---------------------------- | -------------- | ---: | --------------------------------------- |
| `id`                         | BIGSERIAL      |   NO | Идентификатор измерения                 |
| `camera_id`                  | BIGINT         |   NO | FK → cameras.id                         |
| `measured_at`                | TIMESTAMPTZ    |   NO | Время измерения                         |
| `sys_descr`                  | TEXT           |  YES | SNMP sysDescr                           |
| `sys_uptime_ticks`           | BIGINT         |  YES | SNMP uptime                             |
| `sys_name`                   | VARCHAR(255)   |  YES | Имя устройства                          |
| `ip_in_receives`             | BIGINT         |  YES | IP входящие пакеты                      |
| `ip_in_hdr_errors`           | BIGINT         |  YES | Ошибки IP header                        |
| `ip_in_addr_errors`          | BIGINT         |  YES | Ошибки IP address                       |
| `ip_out_requests`            | BIGINT         |  YES | Исходящие IP запросы                    |
| `icmp_in_msgs`               | BIGINT         |  YES | Входящие ICMP                           |
| `icmp_out_echo_reps`         | BIGINT         |  YES | ICMP echo replies                       |
| `mac_address`                | VARCHAR(32)    |  YES | MAC адрес                               |
| `interface_speed`            | BIGINT         |  YES | Скорость интерфейса, bit/s              |
| `active_rtsp_sessions_count` | INTEGER        |  YES | Количество активных RTSP сессий         |
| `scan_duration_ms`           | INTEGER        |  YES | Продолжительность SNMP опроса           |
| `status`                     | VARCHAR(32)    |   NO | Результат SNMP опроса                   |
| `error_message`              | TEXT           |  YES | Ошибка, если опрос завершился неуспешно |

### Индексы

```text
INDEX (camera_id, measured_at)
INDEX (measured_at)
INDEX (status)
```

---

# 6. Таблица `rtsp_clients`

Клиенты, обнаруженные SNMP-опросом.

Связываются не непосредственно с камерой, а с конкретным измерением.

Это важно: состав клиентов меняется со временем.

| Поле                  | Тип PostgreSQL | NULL | Описание                  |
| --------------------- | -------------- | ---: | ------------------------- |
| `id`                  | BIGSERIAL      |   NO | Идентификатор             |
| `snmp_measurement_id` | BIGINT         |   NO | FK → snmp_measurements.id |
| `client_ip`           | INET           |   NO | IP клиента                |
| `client_port`         | INTEGER        |  YES | Порт клиента              |

### Ограничения

```text
PRIMARY KEY (id)
FOREIGN KEY (snmp_measurement_id)
    REFERENCES snmp_measurements(id)
    ON DELETE CASCADE
```

Индекс:

```text
INDEX (snmp_measurement_id)
INDEX (client_ip)
```

Пример исходных данных:

```json
{
    "client_ip": "172.16.140.42",
    "client_port": 50382
}
```

Один IP может иметь несколько одновременных RTSP-сессий с разными портами.

---

# 7. Таблица `wink_measurements`

Одно измерение WINK = один полный запуск `wink-rtsp-stats`.

Исходный WINK результат содержит время запуска, продолжительность, итоговые показатели и информацию о транспортном протоколе.

| Поле                           | Тип PostgreSQL   | NULL | Описание               |
| ------------------------------ | ---------------- | ---: | ---------------------- |
| `id`                           | BIGSERIAL        |   NO | Идентификатор          |
| `camera_id`                    | BIGINT           |   NO | FK → cameras.id        |
| `measured_at`                  | TIMESTAMPTZ      |   NO | Время запуска          |
| `start_time`                   | TIMESTAMPTZ      |  YES | Начало теста           |
| `end_time`                     | TIMESTAMPTZ      |  YES | Конец теста            |
| `duration_s`                   | DOUBLE PRECISION |  YES | Продолжительность      |
| `rtsp_connect_time_ms`         | DOUBLE PRECISION |  YES | Время подключения RTSP |
| `first_rtp_time_ms`            | DOUBLE PRECISION |  YES | Время до первого RTP   |
| `streams_detected`             | INTEGER          |  YES | Количество потоков     |
| `total_bitrate_kbps_avg`       | DOUBLE PRECISION |  YES | Средний общий bitrate  |
| `total_packets`                | BIGINT           |  YES | Всего пакетов          |
| `total_packets_lost_estimated` | BIGINT           |  YES | Оценочные потери       |
| `ssrc_stable`                  | BOOLEAN          |  YES | Стабильность SSRC      |
| `transport_mode`               | VARCHAR(100)     |  YES | Транспорт              |
| `rtcp_received`                | BOOLEAN          |  YES | Получен ли RTCP        |
| `status`                       | VARCHAR(32)      |   NO | Итоговый статус        |
| `error_message`                | TEXT             |  YES | Ошибка запуска/анализа |

### Индексы

```text
INDEX (camera_id, measured_at)
INDEX (measured_at)
INDEX (status)
```

---

# 8. Таблица `wink_streams`

Отдельный RTP-поток внутри одного WINK измерения.

Это необходимо, поскольку один WINK результат может содержать несколько потоков.

| Поле                           | Тип PostgreSQL   | NULL | Описание                  |
| ------------------------------ | ---------------- | ---: | ------------------------- |
| `id`                           | BIGSERIAL        |   NO | Идентификатор             |
| `wink_measurement_id`          | BIGINT           |   NO | FK → wink_measurements.id |
| `ssrc`                         | VARCHAR(32)      |  YES | SSRC                      |
| `media_type`                   | VARCHAR(32)      |  YES | video/audio               |
| `codec`                        | VARCHAR(64)      |  YES | Кодек                     |
| `payload_type`                 | INTEGER          |  YES | RTP payload type          |
| `clock_rate`                   | BIGINT           |  YES | RTP clock rate            |
| `packets_total`                | BIGINT           |  YES | Всего пакетов             |
| `packets_lost_estimated`       | BIGINT           |  YES | Потерянные пакеты         |
| `packets_out_of_order`         | BIGINT           |  YES | Пакеты вне порядка        |
| `packets_duplicated`           | BIGINT           |  YES | Дубликаты                 |
| `jitter_ms_avg`                | DOUBLE PRECISION |  YES | Средний jitter            |
| `jitter_ms_max`                | DOUBLE PRECISION |  YES | Максимальный jitter       |
| `bitrate_kbps_avg`             | DOUBLE PRECISION |  YES | Средний bitrate           |
| `bitrate_kbps_instant`         | DOUBLE PRECISION |  YES | Instant bitrate           |
| `first_seq`                    | BIGINT           |  YES | Первый sequence number    |
| `last_seq`                     | BIGINT           |  YES | Последний sequence number |
| `first_packet_ts`              | TIMESTAMPTZ      |  YES | Первый пакет              |
| `last_packet_ts`               | TIMESTAMPTZ      |  YES | Последний пакет           |
| `burst_avg_per_100ms`          | DOUBLE PRECISION |  YES | Средний burst             |
| `burst_max_per_100ms`          | INTEGER          |  YES | Максимальный burst        |
| `burst_ratio`                  | DOUBLE PRECISION |  YES | Burst ratio               |
| `burst_status`                 | VARCHAR(32)      |  YES | Статус burst              |
| `clock_drift_ms`               | DOUBLE PRECISION |  YES | Clock drift               |
| `clock_drift_trend_ms_per_min` | DOUBLE PRECISION |  YES | Тренд drift               |
| `clock_drift_status`           | VARCHAR(32)      |  YES | Статус drift              |
| `fingerprint`                  | TEXT             |  YES | Fingerprint потока        |

### Индексы

```text
INDEX (wink_measurement_id)
INDEX (ssrc)
INDEX (codec)
```

---

# 9. Статусы WINK

Текущие бизнес-правила сохраняются.

При расчёте итогового статуса:

```text
packet_loss > 10%
    → BAD

total bitrate < 50 kbps
    → STALLED

bitrate < 5 Mbps
    → LOW BITRATE

packet_loss > 2%
    → WARNING

иначе
    → GOOD
```

Порядок проверки должен быть определён явно в сервисном слое, чтобы одинаковый набор входных данных всегда давал одинаковый результат.

---

# 10. Статусы SNMP

Текущие правила проверки:

```text
uptime < 1 дня
    → нарушение

interface_speed < 100 Mbps
    → нарушение
```

Фактический статус измерения должен храниться отдельно от исходных числовых данных.

Исходные значения никогда не заменяются рассчитанным статусом.

---

# 11. Общий статус камеры

Общий статус камеры не является самостоятельным исходным измерением.

Он вычисляется на основании последних результатов SNMP и WINK.

Предварительно:

```text
DISABLED
    камера отключена

OFFLINE
    нет успешного мониторинга

ERROR
    критическая ошибка SNMP или WINK

WARNING
    есть предупреждение

ONLINE
    SNMP и WINK работают штатно

UNKNOWN
    недостаточно данных для определения состояния
```

Конкретный алгоритм приоритета статусов будет реализован в `monitoring_service.py`.

---

# 12. История

История не должна храниться отдельными JSON-файлами.

Каждый запуск мониторинга создаёт новую запись:

```text
cameras
    │
    ├── snmp_measurements
    │       └── rtsp_clients
    │
    └── wink_measurements
            └── wink_streams
```

Последнее измерение используется Dashboard.

Старые измерения используются:

* для истории;
* графиков;
* анализа проблем;
* поиска деградации;
* сравнения периодов;
* расследования инцидентов.

---

# 13. Удаление данных

Удаление камеры должно учитывать связанные исторические данные.

Предпочтительный вариант:

```text
camera
    ↓
не удаляется физически
    ↓
enabled = false
```

Физическое удаление камеры вместе с историей должно быть отдельной административной операцией.

Исторические измерения по возможности сохраняются.

---

# 14. RTSP URL

RTSP URL является параметром камеры.

При этом пароль не должен дублироваться без необходимости в нескольких местах БД.

Целевой принцип:

```text
cameras.rtsp_url
        +
camera_credentials
        ↓
runtime RTSP credentials
```

При миграции существующих данных необходимо сохранить текущую работоспособность WINK.

До реализации механизма нормализации URL запрещается автоматически удалять или изменять пароль в существующих RTSP URL.

---

# 15. Соответствие текущему SNMP JSON

Текущий SNMP результат:

```text
sys_descr
sys_uptime
sys_name
ip_in_receives
ip_in_hdr_errors
ip_in_addr_errors
ip_out_requests
icmp_in_msgs
icmp_out_echo_reps
mac_address_v6
mac_address_v4
interface_speed
active_rtsp_sessions_count
connected_clients[]
tz_number
order_number
rtsp_url
operator
ip
scan_timestamp
```

Преобразуется следующим образом:

```text
tz_number
    → cameras.camera_number

order_number
    → cameras.order_number

rtsp_url
    → cameras.rtsp_url

operator
    → cameras.operator

ip
    → cameras.ip_address

scan_timestamp
    → snmp_measurements.measured_at

sys_descr
    → snmp_measurements.sys_descr

sys_uptime
    → snmp_measurements.sys_uptime_ticks

sys_name
    → snmp_measurements.sys_name

ip_in_receives
    → snmp_measurements.ip_in_receives

ip_in_hdr_errors
    → snmp_measurements.ip_in_hdr_errors

ip_in_addr_errors
    → snmp_measurements.ip_in_addr_errors

ip_out_requests
    → snmp_measurements.ip_out_requests

icmp_in_msgs
    → snmp_measurements.icmp_in_msgs

icmp_out_echo_reps
    → snmp_measurements.icmp_out_echo_reps

mac_address_v6 / mac_address_v4
    → snmp_measurements.mac_address

interface_speed
    → snmp_measurements.interface_speed

active_rtsp_sessions_count
    → snmp_measurements.active_rtsp_sessions_count

connected_clients[]
    → rtsp_clients
```

---

# 16. Соответствие текущему WINK JSON

Основной WINK JSON:

```text
tool
version
schema_version
target
start_time
end_time
duration_s
timing
streams[]
summary
_units
camera_id
order_no
password
operator
```

Преобразование:

```text
camera_id
    → cameras.camera_number / идентификация камеры

order_no
    → cameras.order_number

operator
    → cameras.operator

password
    → camera_credentials.password

start_time
    → wink_measurements.start_time

end_time
    → wink_measurements.end_time

duration_s
    → wink_measurements.duration_s

timing.rtsp_connect_time_ms
    → wink_measurements.rtsp_connect_time_ms

timing.first_rtp_time_ms
    → wink_measurements.first_rtp_time_ms

summary.streams_detected
    → wink_measurements.streams_detected

summary.total_bitrate_kbps_avg
    → wink_measurements.total_bitrate_kbps_avg

summary.total_packets
    → wink_measurements.total_packets

summary.total_packets_lost_estimated
    → wink_measurements.total_packets_lost_estimated

summary.ssrc_stable
    → wink_measurements.ssrc_stable

summary.transport_mode
    → wink_measurements.transport_mode

summary.rtcp_received
    → wink_measurements.rtcp_received

streams[]
    → wink_streams
```

---

# 17. Информация WINK, которую нельзя потерять

При реализации новой системы нельзя ограничиваться только:

```text
bitrate
packet_loss
jitter
```

Необходимо сохранить также:

```text
SSRC
codec
payload_type
clock_rate
packets_total
packets_lost_estimated
packets_out_of_order
packets_duplicated
jitter_ms_avg
jitter_ms_max
bitrate_kbps_avg
bitrate_kbps_instant
first_seq
last_seq
first_packet_ts
last_packet_ts
burst_avg_per_100ms
burst_max_per_100ms
burst_ratio
burst_status
clock_drift_ms
clock_drift_trend_ms_per_min
clock_drift_status
fingerprint
```

Это позволит в дальнейшем строить расширенную диагностику качества RTSP.

---

# 18. Политика хранения исходных данных

База данных должна хранить нормализованные значения.

Не следует складывать весь исходный JSON в одну колонку `jsonb` вместо нормализованных таблиц.

При этом для WINK/SNMP допускается дополнительное поле:

```text
raw_data JSONB
```

если в процессе реализации будет принято решение сохранять оригинальный результат измерения для диагностики и совместимости.

`raw_data` не заменяет нормализованные поля.

---

# 19. Временные зоны

Все даты и время в PostgreSQL хранятся как:

```text
TIMESTAMPTZ
```

Приложение работает с timezone-aware datetime.

Запрещается использовать локальные naive datetime для измерений.

---

# 20. Индексация

Минимальные обязательные индексы:

```text
cameras:
    UNIQUE(camera_number)
    INDEX(ip_address)
    INDEX(enabled)

camera_credentials:
    UNIQUE(camera_id)

snmp_measurements:
    INDEX(camera_id, measured_at)
    INDEX(measured_at)
    INDEX(status)

rtsp_clients:
    INDEX(snmp_measurement_id)
    INDEX(client_ip)

wink_measurements:
    INDEX(camera_id, measured_at)
    INDEX(measured_at)
    INDEX(status)

wink_streams:
    INDEX(wink_measurement_id)
    INDEX(ssrc)
```

Основной запрос Dashboard должен эффективно получать последнее измерение камеры.

---

# 21. ORM

SQLAlchemy-модели должны соответствовать этой схеме.

Предполагаемая структура:

```text
app/
└── models/
    ├── camera.py
    ├── credentials.py
    ├── snmp.py
    ├── rtsp_client.py
    └── wink.py
```

Связи SQLAlchemy:

```text
Camera
 ├── credentials
 ├── snmp_measurements
 │     └── rtsp_clients
 └── wink_measurements
       └── wink_streams
```

---

# 22. Миграции

Изменение структуры БД выполняется только через Alembic.

Запрещается создавать таблицы непосредственно внутри приложения через:

```python
Base.metadata.create_all(...)
```

в production.

Начальная схема должна быть оформлена отдельной Alembic migration.

---

# 23. Что является источником истины

После перехода на PostgreSQL:

```text
PostgreSQL
    ↓
SOURCE OF TRUTH
```

Excel:

```text
cameras.xlsx
    ↓
IMPORT / EXPORT
```

JSON:

```text
JSON
    ↓
DEBUG / EXPORT / MIGRATION
```

Рабочий мониторинг не должен зависеть от наличия JSON-файлов.

---

# 24. Реальные данные, на которых основана схема

Схема разработана на основании фактических результатов текущего SNMP и WINK сборщиков.

SNMP содержит системные показатели, IP/ICMP counters, MAC, скорость интерфейса, количество RTSP-сессий и список подключённых клиентов.

## WINK содержит параметры теста, timing, RTP-потоки, packet statistics, jitter, bitrate, burst analysis, clock drift, SSRC и итоговый transport summary.

# 25. Статус документа

```text
STATUS: APPROVED FOR IMPLEMENTATION

Database schema: DRAFT → ARCHITECTURE BASELINE
Source data: REAL SNMP + WINK JSON
Primary DB: PostgreSQL
ORM: SQLAlchemy
Migrations: Alembic
```

Изменения структуры после начала реализации должны сопровождаться изменением этого документа и соответствующей Alembic migration.
