# Monitoring RSVN — TODO.md

> Дорожная карта полной переработки проекта.
>
> Статусы:
>
> * `[ ]` — не выполнено
> * `[~]` — выполняется
> * `[x]` — выполнено
> * `[!]` — блокирующий вопрос / требуется решение
> * `[?]` — требуется дополнительное исследование
>
> Ответственные:
>
> * `AI` — выполняет ИИ-агент
> * `DEV` — действие/решение разработчика
> * `AI+DEV` — совместная работа
>
> **Критическое правило:** пароли камер и RTSP credentials НЕ удаляются из проекта. Они должны продолжить храниться в системе и использоваться мониторингом.

---

# 0. Цели проекта

* [ ] `AI+DEV` Перевести результаты мониторинга с JSON-файлов на полноценную СУБД.
* [ ] `AI+DEV` Выбрать PostgreSQL как основную СУБД.
* [ ] `AI` Переделать архитектуру проекта в модульную структуру.
* [ ] `AI` Объединить SNMP и WINK в единый backend.
* [ ] `AI` Создать единый Web UI.
* [ ] `AI` Создать интерфейс управления камерами.
* [ ] `AI` Создать историю результатов мониторинга.
* [ ] `AI` Перевести SNMP на чистый asyncio.
* [ ] `AI` Устранить архитектурную проблему `ThreadPoolExecutor + asyncio` в SNMP.
* [ ] `AI` Сохранить ограничение параллельных WINK-проверок, но вынести его в конфигурацию.
* [ ] `AI` Добавить нормальное управление зависимостями Python.
* [ ] `AI` Добавить конфигурацию вместо hardcoded settings.
* [ ] `AI` Добавить logging.
* [ ] `AI` Добавить миграции БД.
* [ ] `AI` Добавить тесты.
* [ ] `AI` Подготовить запуск через systemd.
* [ ] `AI+DEV` Провести финальный аудит после миграции.

---

# 1. Зафиксированное состояние текущего проекта

## 1.1 Текущая структура

Текущий проект состоит из четырёх основных скриптов:

```text
scan-snmp.py
scan-wink.py
generate-snmp-report.py
generate-wink-report.py
```

Текущий поток:

```text
cameras.xlsx
    │
    ├── scan-snmp.py
    │       │
    │       └── scanned_metrics/*.json
    │                │
    │                └── generate-snmp-report.py
    │                         │
    │                         └── report-snmp.html
    │
    └── scan-wink.py
            │
            └── metrics_json/*.json
                     │
                     └── generate-wink-report.py
                              │
                              └── report-wink.html
```

---

# 2. Инвентаризация текущего SNMP

## 2.1 SNMP settings

Текущий код содержит:

```text
COMMUNITY = "public"
SNMP_PORT = 161
TIMEOUT = 2.0
RETRIES = 1
MAX_THREADS = 50
```

Также hardcoded:

```text
ExceptOurNetworks = 0

OurIp:
    10.35.2.0/24
    10.0.70.10
```

Задача:

* [ ] `AI` Перенести настройки в конфигурацию.
* [ ] `AI` Убрать `MAX_THREADS`.
* [ ] `AI` Заменить его на ограничение asyncio concurrency.
* [ ] `AI` Перенести `OurIp` в конфигурацию.
* [ ] `AI` Перенести `ExceptOurNetworks` в конфигурацию.
* [ ] `AI` Перенести SNMP timeout/retries в конфигурацию.
* [ ] `AI+DEV` Определить, хранится ли SNMP community глобально или индивидуально для камеры.

---

# 3. Данные SNMP

Текущий SNMP собирает:

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
```

Для каждого клиента:

```text
client_ip
client_port
```

Также сохраняются:

```text
tz_number
order_number
rtsp_url
operator
ip
scan_timestamp
```

Задачи:

* [ ] `AI` Составить окончательную модель SNMP measurement.
* [ ] `AI` Определить тип каждого значения PostgreSQL.
* [ ] `AI` Не хранить числовые значения как строки без необходимости.
* [ ] `AI` Сохранять timestamp средствами БД.
* [ ] `AI` Отделить metadata камеры от результатов измерения.
* [ ] `AI` Сохранить информацию об активных RTSP-клиентах.
* [ ] `AI` Определить модель хранения списка `connected_clients`.
* [ ] `AI` Решить, нужны ли отдельные записи для каждого RTSP-клиента.

---

# 4. Полный переход SNMP на asyncio

## Текущее состояние

Сейчас используется:

```text
ThreadPoolExecutor(max_workers=50)
        │
        ├── thread
        │      └── asyncio.run(...)
        │
        ├── thread
        │      └── asyncio.run(...)
        │
        └── ...
```

Это необходимо переделать.

## Целевая архитектура

```text
asyncio event loop
        │
        ├── camera #1
        ├── camera #2
        ├── camera #3
        ├── ...
        └── camera #N

asyncio.Semaphore(N)
```

Задачи:

* [ ] `AI` Удалить `ThreadPoolExecutor` из SNMP.
* [ ] `AI` Удалить `process_camera_in_thread()`.
* [ ] `AI` Создать единый async worker.
* [ ] `AI` Создать `asyncio.Semaphore`.
* [ ] `AI` Ограничивать одновременно выполняющиеся SNMP операции через semaphore.
* [ ] `AI` Корректно создавать/закрывать `SnmpEngine`.
* [ ] `AI` Обеспечить корректную обработку timeout.
* [ ] `AI` Обеспечить корректную обработку SNMP error status.
* [ ] `AI` Не использовать `except Exception: pass`.
* [ ] `AI` Добавить диагностическое логирование.
* [ ] `AI` Проверить совместимость с текущей PySNMP 7.x API.
* [ ] `AI` Проверить корректность SNMP TCP table walk после переписывания.
* [ ] `AI` Провести нагрузочный тест на большом количестве камер.

---

# 5. WINK / RTSP

## Текущее состояние

WINK использует:

```text
ThreadPoolExecutor(max_workers=4)
        │
        └── subprocess.run()
                │
                └── wink-rtsp-stats.exe
```

В отличие от SNMP это не нужно бездумно переводить в asyncio.

Причина:

`wink-rtsp-stats.exe` — внешний блокирующий процесс.

Целевой вариант:

```text
async application
       │
       └── bounded process execution
              │
              └── wink-rtsp-stats.exe
```

Задачи:

* [ ] `AI` Оставить ограничение количества одновременных WINK-проверок.
* [ ] `AI` Переименовать `MAX_WORKERS` в более точный параметр concurrency.
* [ ] `AI` Вынести значение в конфигурацию.
* [ ] `AI` Вынести путь к `wink-rtsp-stats.exe` в конфигурацию.
* [ ] `AI` Обработать отсутствие executable.
* [ ] `AI` Обработать ненулевой exit code.
* [ ] `AI` Обработать timeout внешнего процесса.
* [ ] `AI` Не блокировать основной worker бесконтрольно.
* [ ] `AI` Сохранять результат WINK непосредственно в PostgreSQL.
* [ ] `AI` Сохранить raw output при необходимости диагностики.
* [ ] `AI` Проверить, нужно ли хранить raw output постоянно или только при ошибке.

---

# 6. WINK данные

Текущая логика использует:

```text
camera_id
order_no
password
operator
target
```

Из WINK metrics:

```text
total_bitrate_kbps_avg
total_packets
total_packets_lost_estimated
jitter_ms_avg
streams[]
```

Рассчитываются:

```text
bitrate Mbps
packet loss %
jitter
```

Статусы:

```text
BAD
STALLED
LOW BITRATE
WARNING
GOOD
```

Задачи:

* [ ] `AI` Формализовать модель WINK measurement.
* [ ] `AI` Перенести расчёт bitrate в backend.
* [ ] `AI` Перенести расчёт packet loss в backend.
* [ ] `AI` Перенести расчёт jitter в backend.
* [ ] `AI` Формализовать status enum.
* [ ] `AI` Вынести thresholds в конфигурацию.
* [ ] `AI` Сохранять timestamp каждого измерения.
* [ ] `AI` Сохранять результат каждого stream при необходимости.
* [ ] `AI` Определить модель таблицы `wink_stream_measurements`.

---

# 7. PostgreSQL

## Решение

Основная СУБД:

```text
PostgreSQL
```

Не использовать JSON-файлы как основное хранилище результатов.

Задачи:

* [ ] `AI` Создать PostgreSQL schema.
* [ ] `AI` Создать SQLAlchemy models.
* [ ] `AI` Создать Alembic migrations.
* [ ] `AI` Создать initial migration.
* [ ] `AI` Добавить индексы.
* [ ] `AI` Добавить foreign keys.
* [ ] `AI` Добавить timestamps.
* [ ] `AI` Добавить constraints.
* [ ] `AI` Проверить cascade/update/delete поведение.

---

# 8. Предварительная модель БД

## cameras

Предварительно:

```text
cameras
---------
id
camera_number
name
ip_address
manufacturer
model
operator
order_number
rtsp_url
enabled
created_at
updated_at
```

Задачи:

* [ ] `AI` Уточнить обязательные поля.
* [ ] `AI` Определить unique constraints.
* [ ] `AI` Определить формат IP.
* [ ] `AI` Определить формат camera_number.
* [ ] `AI` Добавить enabled/disabled.
* [ ] `AI` Добавить description/notes при необходимости.

---

# 9. Credentials

Пароли сохраняем.

Предварительно:

```text
camera_credentials
------------------
id
camera_id
username
password
snmp_community
created_at
updated_at
```

Задачи:

* [ ] `AI+DEV` Подтвердить окончательную модель credentials.
* [ ] `AI` Сохранить password.
* [ ] `AI` Сохранить username.
* [ ] `AI` Сохранить SNMP community.
* [ ] `AI` Не удалять credentials из рабочего процесса.
* [ ] `AI` Не выводить пароль в обычные списки без необходимости.
* [ ] `AI` Сохранить возможность копирования пароля через UI.
* [ ] `AI+DEV` Отдельно решить вопрос шифрования credentials.
* [ ] `AI` Не делать шифрование обязательным условием текущего этапа.

---

# 10. SNMP measurements

Предварительно:

```text
snmp_measurements
-----------------
id
camera_id
measured_at

sys_descr
sys_uptime_ticks
sys_name

ip_in_receives
ip_in_hdr_errors
ip_in_addr_errors
ip_out_requests

icmp_in_msgs
icmp_out_echo_reps

mac_address
interface_speed

active_rtsp_sessions_count
```

Задачи:

* [ ] `AI` Уточнить типы всех полей.
* [ ] `AI` Сохранить исходное uptime в ticks.
* [ ] `AI` При необходимости хранить calculated uptime.
* [ ] `AI` Уточнить MAC storage format.
* [ ] `AI` Добавить indexes `(camera_id, measured_at)`.
* [ ] `AI` Добавить индекс `measured_at`.
* [ ] `AI` Продумать retention.

---

# 11. RTSP clients

Возможный вариант:

```text
rtsp_clients
------------
id
snmp_measurement_id
client_ip
client_port
```

Задачи:

* [ ] `AI` Определить, нужен ли отдельный table.
* [ ] `AI` Если нужен — создать relationship с SNMP measurement.
* [ ] `AI` Добавить индекс по measurement_id.
* [ ] `AI` Сохранить историю подключений.

---

# 12. WINK measurements

Предварительно:

```text
wink_measurements
-----------------
id
camera_id
measured_at

status
bitrate_kbps
packet_loss_percent
jitter_ms

total_packets
lost_packets
```

Задачи:

* [ ] `AI` Уточнить все поля.
* [ ] `AI` Добавить thresholds/config.
* [ ] `AI` Добавить indexes `(camera_id, measured_at)`.
* [ ] `AI` Определить retention.
* [ ] `AI` Определить хранение raw result.

---

# 13. История

Главное отличие новой системы от текущей:

Сейчас:

```text
camera.json
```

перезаписывается.

После переделки:

```text
camera
  │
  ├── measurement 10:00
  ├── measurement 10:05
  ├── measurement 10:10
  ├── measurement 10:15
  └── ...
```

Задачи:

* [ ] `AI` Хранить историю SNMP.
* [ ] `AI` Хранить историю WINK.
* [ ] `AI` Добавить запрос последнего состояния.
* [ ] `AI` Добавить запрос истории за период.
* [ ] `AI` Добавить retention policy.
* [ ] `AI+DEV` Определить срок хранения подробных measurements.
* [ ] `AI` Не удалять историю автоматически до согласования retention.

---

# 14. Удаление JSON storage

После успешной миграции:

* [ ] `AI` Убрать `scanned_metrics/` как persistent storage.
* [ ] `AI` Убрать `metrics_json/` как persistent storage.
* [ ] `AI` Убрать запись SNMP JSON.
* [ ] `AI` Убрать запись WINK JSON.
* [ ] `AI` Убрать чтение JSON из report generators.
* [ ] `AI` Проверить, что JSON не используется как скрытая БД.
* [ ] `AI` При необходимости оставить JSON только для debug/export.

---

# 15. Excel

Сейчас:

```text
cameras.xlsx
```

является фактическим источником конфигурации камер.

После переделки:

```text
PostgreSQL
    ↑
Web UI
```

Excel становится вспомогательным инструментом.

Задачи:

* [ ] `AI` Реализовать импорт камер из XLSX.
* [ ] `AI` Сопоставить колонки старого XLSX с новой schema.
* [ ] `AI` Не создавать дубликаты при повторном импорте.
* [ ] `AI` Добавить валидацию XLSX.
* [ ] `AI` Реализовать экспорт камер в XLSX.
* [ ] `AI` После миграции убрать обязательную зависимость runtime от `cameras.xlsx`.
* [ ] `DEV` Предоставить актуальный пример `cameras.xlsx`, если формат отличается от текущего.

---

# 16. Backend

Предлагаемый стек:

```text
FastAPI
SQLAlchemy
Alembic
PostgreSQL
Pydantic
Uvicorn
```

Задачи:

* [ ] `AI` Создать FastAPI application.
* [ ] `AI` Создать application factory/entry point.
* [ ] `AI` Создать database session management.
* [ ] `AI` Создать API routers.
* [ ] `AI` Создать services layer.
* [ ] `AI` Отделить database access от business logic.
* [ ] `AI` Добавить `/api/health`.
* [ ] `AI` Добавить OpenAPI documentation.
* [ ] `AI` Проверить graceful shutdown.

---

# 17. API камер

Минимальный API:

```text
GET    /api/cameras
POST   /api/cameras

GET    /api/cameras/{id}
PUT    /api/cameras/{id}
DELETE /api/cameras/{id}

POST   /api/cameras/{id}/test-snmp
POST   /api/cameras/{id}/test-rtsp

POST   /api/cameras/import
GET    /api/cameras/export
```

Задачи:

* [ ] `AI` Реализовать GET cameras.
* [ ] `AI` Реализовать создание камеры.
* [ ] `AI` Реализовать редактирование.
* [ ] `AI` Реализовать удаление.
* [ ] `AI` Реализовать enable/disable.
* [ ] `AI` Реализовать ручной SNMP test.
* [ ] `AI` Реализовать ручной RTSP test.
* [ ] `AI` Реализовать импорт XLSX.
* [ ] `AI` Реализовать экспорт XLSX.

---

# 18. API мониторинга

Предварительно:

```text
GET /api/monitoring/summary

GET /api/cameras/{id}/status
GET /api/cameras/{id}/snmp
GET /api/cameras/{id}/wink

GET /api/cameras/{id}/history/snmp
GET /api/cameras/{id}/history/wink

GET /api/problems
```

Задачи:

* [ ] `AI` Реализовать summary.
* [ ] `AI` Реализовать current camera status.
* [ ] `AI` Реализовать SNMP current state.
* [ ] `AI` Реализовать WINK current state.
* [ ] `AI` Реализовать historical queries.
* [ ] `AI` Реализовать список проблем.

---

# 19. Единый статус камеры

Ввести:

```text
ONLINE
WARNING
ERROR
OFFLINE
DISABLED
UNKNOWN
```

При этом отдельно:

```text
snmp_status
rtsp_status
overall_status
```

Пример:

```text
Overall: WARNING
SNMP: GOOD
RTSP: WARNING
```

Задачи:

* [ ] `AI` Формализовать enum.
* [ ] `AI` Формализовать правила расчёта.
* [ ] `AI` Перенести правила из HTML в backend.
* [ ] `AI` Добавить unit tests на status calculation.

---

# 20. Web UI

Единый интерфейс:

```text
Dashboard
Cameras
SNMP
RTSP/WINK
History
Problems
Settings
```

Задачи:

* [ ] `AI` Создать dashboard.
* [ ] `AI` Создать список камер.
* [ ] `AI` Создать карточку/страницу камеры.
* [ ] `AI` Создать SNMP section.
* [ ] `AI` Создать RTSP/WINK section.
* [ ] `AI` Создать history charts.
* [ ] `AI` Создать Problems page.
* [ ] `AI` Создать Settings page.
* [ ] `AI` Добавить поиск.
* [ ] `AI` Добавить фильтры.
* [ ] `AI` Добавить сортировку.
* [ ] `AI` Добавить pagination.
* [ ] `AI` Добавить auto-refresh.
* [ ] `AI` Добавить ручное обновление.

---

# 21. Dashboard

Dashboard должен показывать:

```text
Всего камер
Активных
Disabled

SNMP GOOD
SNMP WARNING
SNMP OFFLINE

RTSP GOOD
RTSP WARNING
RTSP ERROR

Общее количество проблем
Worker status
Последний scan
Следующий scan
```

Задачи:

* [ ] `AI` Реализовать summary cards.
* [ ] `AI` Реализовать таблицу текущего состояния.
* [ ] `AI` Реализовать быстрые фильтры.
* [ ] `AI` Реализовать список критических проблем.
* [ ] `AI` Реализовать время последнего обновления.

---

# 22. Страница камеры

Должна содержать:

```text
Камера
IP
Модель
Производитель
Оператор
Номер заказа
RTSP URL
Credentials

SNMP
    Uptime
    MAC
    Interface speed
    Traffic
    Errors
    Active sessions

RTSP/WINK
    Bitrate
    Packet loss
    Jitter
    Stream status

History
```

Задачи:

* [ ] `AI` Реализовать camera details.
* [ ] `AI` Реализовать monitoring details.
* [ ] `AI` Реализовать history.
* [ ] `AI` Реализовать actions.
* [ ] `AI` Добавить edit camera.
* [ ] `AI` Добавить manual tests.

---

# 23. Управление камерами

CRUD:

```text
CREATE
READ
UPDATE
DELETE
```

Поля:

```text
camera number
name
IP
manufacturer
model
operator
order number
RTSP URL
username
password
SNMP community
enabled
```

Задачи:

* [ ] `AI` Форма добавления.
* [ ] `AI` Форма редактирования.
* [ ] `AI` Удаление.
* [ ] `AI` Enable/disable.
* [ ] `AI` Validation.
* [ ] `AI` Duplicate detection.
* [ ] `AI` Confirmation before delete.

---

# 24. Credentials UI

Пароли НЕ удалять.

Задачи:

* [ ] `AI` Добавить password field.
* [ ] `AI` Добавить username.
* [ ] `AI` Добавить SNMP community.
* [ ] `AI` Возможность показать/скрыть пароль.
* [ ] `AI` Возможность копирования.
* [ ] `AI` Не показывать password в dashboard.
* [ ] `AI` Не включать password в обычный поиск.
* [ ] `AI+DEV` Позже рассмотреть encryption-at-rest.

---

# 25. Конфигурация

Не хранить runtime settings в Python.

Создать:

```text
.env
.env.example
config/
    config.yaml
```

Предварительные параметры:

```text
DATABASE_URL

SNMP_PORT
SNMP_TIMEOUT
SNMP_RETRIES
SNMP_CONCURRENCY

WINK_EXECUTABLE
WINK_CONCURRENCY
WINK_MEASURE_DURATION

MONITORING_INTERVAL

RETENTION_DAYS
```

Задачи:

* [ ] `AI` Создать configuration layer.
* [ ] `AI` Создать Pydantic settings.
* [ ] `AI` Создать `.env.example`.
* [ ] `AI` Убрать hardcoded runtime settings.
* [ ] `AI` Проверить отсутствие секретов в Git.
* [ ] `DEV` Указать production values перед deployment.

---

# 26. Paths

Сейчас используются относительные пути:

```text
cameras.xlsx
scanned_metrics
metrics_json
report-snmp.html
report-wink.html
```

Задачи:

* [ ] `AI` Убрать зависимость от текущего working directory.
* [ ] `AI` Убрать JSON directories после миграции.
* [ ] `AI` Убрать runtime dependency от HTML files.
* [ ] `AI` Определить единый application root.
* [ ] `AI` Проверить работу при запуске через systemd.

---

# 27. Dependencies

Создать:

```text
pyproject.toml
```

или согласованный dependency file.

Минимальный ожидаемый стек:

```text
fastapi
uvicorn
sqlalchemy
alembic
asyncpg
pydantic
pydantic-settings
pysnmp
openpyxl
```

Задачи:

* [ ] `AI` Определить фактические зависимости.
* [ ] `AI` Удалить неиспользуемые зависимости.
* [ ] `AI` Зафиксировать совместимые версии.
* [ ] `AI` Создать pyproject.toml.
* [ ] `AI` Проверить чистую установку.
* [ ] `AI` Проверить запуск в чистом virtualenv.
* [ ] `AI` Документировать установку.

---

# 28. Logging

Заменить:

```text
print()
except Exception: pass
```

на:

```text
logging
```

Задачи:

* [ ] `AI` Создать logging configuration.
* [ ] `AI` Добавить INFO.
* [ ] `AI` Добавить WARNING.
* [ ] `AI` Добавить ERROR.
* [ ] `AI` Добавить DEBUG.
* [ ] `AI` Добавить camera identifier в log context.
* [ ] `AI` Добавить scan identifier.
* [ ] `AI` Убрать silent exception swallowing.
* [ ] `AI` Проверить systemd journal output.

---

# 29. Error handling

Проблемные места текущего проекта:

```text
except Exception:
    pass
```

и слишком широкие обработчики.

Задачи:

* [ ] `AI` Найти все broad exception handlers.
* [ ] `AI` Разделить ожидаемые и неожиданные ошибки.
* [ ] `AI` Добавить понятные error types.
* [ ] `AI` Логировать traceback там, где это необходимо.
* [ ] `AI` Не прекращать весь monitoring из-за одной камеры.
* [ ] `AI` Сохранять failed measurement.
* [ ] `AI` Устанавливать корректный camera status при timeout.

---

# 30. Worker architecture

Целевая архитектура:

```text
PostgreSQL
    ▲
    │
Monitoring Worker
    │
    ├── SNMP asyncio
    │
    └── WINK process execution
```

Отдельно:

```text
FastAPI Web
    │
    ▼
PostgreSQL
```

Задачи:

* [ ] `AI` Создать monitoring worker.
* [ ] `AI` Сделать worker независимым от Web UI.
* [ ] `AI` Добавить monitoring interval.
* [ ] `AI` Добавить graceful shutdown.
* [ ] `AI` Добавить worker heartbeat.
* [ ] `AI` Защититься от двойного запуска worker.
* [ ] `AI` Добавить worker health state в БД/API.

---

# 31. Systemd

Предлагается два сервиса:

```text
monitoring-rsvn-web.service
monitoring-rsvn-worker.service
```

Задачи:

* [ ] `AI` Создать systemd unit для Web.
* [ ] `AI` Создать systemd unit для Worker.
* [ ] `AI` Настроить WorkingDirectory.
* [ ] `AI` Настроить User.
* [ ] `AI` Настроить EnvironmentFile.
* [ ] `AI` Настроить Restart policy.
* [ ] `AI` Проверить запуск после reboot.
* [ ] `AI` Проверить journalctl.
* [ ] `AI` Проверить graceful restart.

---

# 32. Security

Пароли сохраняются, но система должна обращаться с ними осознанно.

Задачи:

* [ ] `AI` Не писать credentials в application logs.
* [ ] `AI` Не писать credentials в обычные monitoring logs.
* [ ] `AI` Не включать password в dashboard table.
* [ ] `AI` Не включать password в search.
* [ ] `AI` Не отправлять password клиенту без необходимости.
* [ ] `AI` Проверить RTSP URL на наличие credentials.
* [ ] `AI` Не логировать полный RTSP URL, если он содержит password.
* [ ] `AI+DEV` Определить требования к encryption-at-rest.
* [ ] `AI` Проверить `.gitignore`.

---

# 33. Excel export

Текущий UI умеет экспортировать таблицу.

Новая система должна сохранить эту возможность.

Задачи:

* [ ] `AI` Реализовать export cameras.
* [ ] `AI` Реализовать export monitoring results.
* [ ] `AI` Реализовать export filtered results.
* [ ] `AI` Решить, экспортировать ли credentials.
* [ ] `DEV` Подтвердить необходимость экспорта password.

---

# 34. SheetJS

Текущие отчёты используют:

```text
xlsx.full.min.js
```

при этом файл не является частью текущей структуры проекта.

Задачи:

* [ ] `AI` Убрать зависимость старых report generators.
* [ ] `AI` Реализовать Excel export backend/frontend корректным способом.
* [ ] `AI` Не зависеть от отсутствующего локального JS файла.
* [ ] `AI` Проверить экспорт после миграции.

---

# 35. Accessibility / UI

Сохранить полезную функцию color-blind mode из текущего WINK report.

Задачи:

* [ ] `AI` Перенести color-blind mode.
* [ ] `AI` Не полагаться только на цвет для статуса.
* [ ] `AI` Использовать текстовые статусы.
* [ ] `AI` Добавить понятные icons/labels.
* [ ] `AI` Проверить responsive layout.

---

# 36. Performance

Задачи:

* [ ] `AI` Добавить database indexes.
* [ ] `AI` Не загружать всю историю камеры сразу.
* [ ] `AI` Использовать pagination.
* [ ] `AI` Ограничивать history query.
* [ ] `AI` Использовать async DB access.
* [ ] `AI` Проверить PostgreSQL connection pool.
* [ ] `AI` Проверить SNMP concurrency.
* [ ] `AI` Проверить WINK concurrency.
* [ ] `AI` Провести нагрузочный тест.

---

# 37. Tests

Создать:

```text
tests/
├── test_camera.py
├── test_snmp.py
├── test_wink.py
├── test_status.py
├── test_database.py
├── test_api.py
└── test_import.py
```

Задачи:

* [ ] `AI` Unit tests для camera model.
* [ ] `AI` Unit tests для status calculation.
* [ ] `AI` Unit tests для uptime parser.
* [ ] `AI` Unit tests для MAC parser.
* [ ] `AI` Unit tests для speed parser.
* [ ] `AI` Unit tests для RTSP IP extraction.
* [ ] `AI` Unit tests для packet loss calculation.
* [ ] `AI` Tests SNMP error handling.
* [ ] `AI` Tests WINK error handling.
* [ ] `AI` API tests.
* [ ] `AI` Database integration tests.
* [ ] `AI` XLSX import tests.

---

# 38. Перенос старых алгоритмов

Не потерять существующую бизнес-логику.

## SNMP

Сохранить:

* [ ] `AI` scalar OID collection.
* [ ] `AI` TCP table walk.
* [ ] `AI` RTSP port 554 detection.
* [ ] `AI` filtering собственных сетей.
* [ ] `AI` active clients.
* [ ] `AI` uptime.
* [ ] `AI` interface speed.
* [ ] `AI` MAC.
* [ ] `AI` IP counters.

## WINK

Сохранить:

* [ ] `AI` внешний `wink-rtsp-stats.exe`.
* [ ] `AI` measurement duration.
* [ ] `AI` bitrate calculation.
* [ ] `AI` packet loss calculation.
* [ ] `AI` jitter calculation.
* [ ] `AI` stream parsing.
* [ ] `AI` status thresholds.

---

# 39. Business rules

Текущие SNMP критерии:

```text
Uptime < 1 день
OR
Interface speed < 100 Mbps
```

Задачи:

* [ ] `AI` Перенести в backend.
* [ ] `AI` Сделать thresholds конфигурируемыми.
* [ ] `AI` Добавить тесты.

Текущие WINK критерии:

```text
loss > 10%       => BAD

bitrate < 50 kbps
                  => STALLED

bitrate < 5 Mbps => LOW BITRATE

loss > 2%        => WARNING

иначе             => GOOD
```

Задачи:

* [ ] `AI` Перенести в backend.
* [ ] `AI` Сделать thresholds конфигурируемыми.
* [ ] `AI` Добавить тесты.

---

# 40. Новая структура проекта

Предварительная структура:

```text
monitoring-rsvn/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── logging_config.py
│   │
│   ├── models/
│   │   ├── camera.py
│   │   ├── credentials.py
│   │   ├── snmp.py
│   │   ├── wink.py
│   │   └── rtsp_client.py
│   │
│   ├── schemas/
│   │   ├── camera.py
│   │   ├── monitoring.py
│   │   └── reports.py
│   │
│   ├── services/
│   │   ├── camera_service.py
│   │   ├── snmp_service.py
│   │   ├── wink_service.py
│   │   └── monitoring_service.py
│   │
│   ├── scanners/
│   │   ├── snmp_scanner.py
│   │   └── wink_scanner.py
│   │
│   ├── api/
│   │   ├── cameras.py
│   │   ├── monitoring.py
│   │   ├── history.py
│   │   └── health.py
│   │
│   ├── web/
│   │   ├── templates/
│   │   └── static/
│   │
│   └── utils/
│       ├── parsing.py
│       ├── network.py
│       └── formatting.py
│
├── migrations/
│
├── tests/
│
├── config/
│   └── config.yaml
│
├── systemd/
│   ├── monitoring-rsvn-web.service
│   └── monitoring-rsvn-worker.service
│
├── scripts/
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
└── TODO.md
```

Задачи:

* [ ] `AI` Финализировать структуру.
* [ ] `AI` Создать directories.
* [ ] `AI` Перенести код по ответственности.
* [ ] `AI` Удалить монолитные старые scripts после миграции.
* [ ] `AI` Обновить README.

---

# 41. Порядок реализации

## Phase 1 — Architecture

* [x] `AI` Провести аудит текущего проекта.
* [x] `AI` Зафиксировать текущие четыре скрипта.
* [x] `AI` Зафиксировать текущие данные SNMP.
* [x] `AI` Зафиксировать текущие данные WINK.
* [x] `AI` Зафиксировать текущие business rules.
* [ ] `AI` Финализировать schema БД.
* [ ] `AI+DEV` Утвердить schema БД.

## Phase 2 — Database

* [ ] `AI` PostgreSQL setup.
* [ ] `AI` SQLAlchemy.
* [ ] `AI` Alembic.
* [ ] `AI` Initial migration.
* [ ] `AI` Indexes.
* [ ] `AI` Constraints.
* [ ] `AI` DB tests.

## Phase 3 — Configuration

* [ ] `AI` pyproject.toml.
* [ ] `AI` config layer.
* [ ] `AI` `.env.example`.
* [ ] `AI` Remove hardcoded settings.

## Phase 4 — SNMP

* [ ] `AI` Async architecture.
* [ ] `AI` Semaphore.
* [ ] `AI` SNMP scanner.
* [ ] `AI` Database persistence.
* [ ] `AI` Error handling.
* [ ] `AI` Tests.

## Phase 5 — WINK

* [ ] `AI` WINK service.
* [ ] `AI` External process management.
* [ ] `AI` Concurrency control.
* [ ] `AI` Database persistence.
* [ ] `AI` Tests.

## Phase 6 — Backend

* [ ] `AI` FastAPI.
* [ ] `AI` Camera API.
* [ ] `AI` Monitoring API.
* [ ] `AI` History API.
* [ ] `AI` Health API.

## Phase 7 — Web UI

* [ ] `AI` Dashboard.
* [ ] `AI` Cameras.
* [ ] `AI` Camera details.
* [ ] `AI` SNMP.
* [ ] `AI` RTSP/WINK.
* [ ] `AI` History.
* [ ] `AI` Problems.
* [ ] `AI` Settings.
* [ ] `AI` CRUD cameras.
* [ ] `AI` Import XLSX.
* [ ] `AI` Export XLSX.

## Phase 8 — Worker

* [ ] `AI` Monitoring scheduler.
* [ ] `AI` SNMP async scan.
* [ ] `AI` WINK scan.
* [ ] `AI` DB persistence.
* [ ] `AI` Worker health.
* [ ] `AI` Graceful shutdown.
* [ ] `AI` Duplicate-run protection.

## Phase 9 — Deployment

* [ ] `AI` systemd Web service.
* [ ] `AI` systemd Worker service.
* [ ] `AI` Environment configuration.
* [ ] `AI` Logging.
* [ ] `AI` Restart policy.
* [ ] `AI` Reboot test.

## Phase 10 — Final QA

* [ ] `AI` Syntax check.
* [ ] `AI` Import check.
* [ ] `AI` Unit tests.
* [ ] `AI` Integration tests.
* [ ] `AI` Database tests.
* [ ] `AI` SNMP tests.
* [ ] `AI` WINK tests.
* [ ] `AI` API tests.
* [ ] `AI` UI tests.
* [ ] `AI` Load test.
* [ ] `AI` Security audit.
* [ ] `AI` Architecture audit.
* [ ] `AI+DEV` Production acceptance test.

---

# 42. Definition of Done

Проект считается переработанным только если одновременно выполнены все условия:

* [ ] PostgreSQL является основным хранилищем.
* [ ] JSON не используется как постоянное хранилище.
* [ ] Камеры управляются через Web UI.
* [ ] Excel не является обязательным runtime dependency.
* [ ] SNMP работает через чистый asyncio.
* [ ] SNMP не использует ThreadPoolExecutor.
* [ ] WINK имеет контролируемый concurrency.
* [ ] WINK продолжает работать через `wink-rtsp-stats.exe`.
* [ ] Все результаты сохраняются в PostgreSQL.
* [ ] История measurements доступна через UI.
* [ ] Есть единый Dashboard.
* [ ] Есть единая страница камеры.
* [ ] Есть SNMP + RTSP/WINK в одном интерфейсе.
* [ ] Есть CRUD камер.
* [ ] Пароли сохранены и доступны системе.
* [ ] Credentials не попадают случайно в обычные логи.
* [ ] Есть configuration layer.
* [ ] Есть dependency management.
* [ ] Есть Alembic migrations.
* [ ] Есть logging.
* [ ] Есть tests.
* [ ] Есть health check.
* [ ] Есть systemd services.
* [ ] После reboot система автоматически запускается.
* [ ] Worker и Web работают независимо.
* [ ] Нет зависимости от текущего working directory.
* [ ] README соответствует новой архитектуре.
* [ ] Старые HTML report generators больше не являются частью runtime.
* [ ] Финальный аудит пройден.

---

# 43. Правило работы AI-агента

Перед изменением архитектурно значимого компонента:

1. Проверить этот TODO.
2. Проверить фактическое состояние репозитория.
3. Не считать пункт `[x]`, пока изменение не проверено.
4. После каждого завершённого этапа обновлять статус.
5. Не удалять старую реализацию до появления новой рабочей реализации.
6. Не ломать существующую SNMP/WINK бизнес-логику без фиксации изменения.
7. Не удалять passwords.
8. Не считать отсутствие ошибки запуска доказательством корректности.
9. После каждого крупного этапа выполнять тесты.
10. Перед финальным удалением старого кода провести regression check.

---

# 44. Текущая точка проекта

**Текущий статус:**

```text
Аудит исходного проекта       DONE
Целевая архитектура           DEFINED
Схема БД                      DRAFT
Web UI концепция              DEFINED
SNMP asyncio migration        TODO
WINK migration                TODO
FastAPI                       TODO
PostgreSQL                    TODO
Alembic                       TODO
CRUD cameras                  TODO
History                       TODO
systemd                       TODO
Tests                         TODO
Final QA                      TODO
```

**Следующее действие:**

> Спроектировать и утвердить окончательную PostgreSQL schema на основании фактических полей текущих SNMP/WINK результатов, после чего создать SQLAlchemy models и Alembic initial migration.

**Важно:** до завершения этого этапа не начинать массовый рефакторинг четырёх старых файлов.
