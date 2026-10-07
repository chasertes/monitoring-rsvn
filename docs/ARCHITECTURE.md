# Architecture

## 1. Назначение

Этот документ описывает целевую архитектуру проекта `monitoring-rsvn`.

Архитектура разделяет:

* Web UI и HTTP API;
* бизнес-логику;
* сервисы;
* сканеры мониторинга;
* PostgreSQL;
* web-процесс;
* worker-процесс.

Целевая архитектура заменяет текущий скриптовый подход на модульное приложение, сохраняя существующую логику мониторинга SNMP и WINK.

---

## 2. Общая архитектура

```text
                         Browser
                            |
                            v
                     +-------------+
                     |   FastAPI   |
                     |  Web / API  |
                     +------+------+
                            |
                            v
                     +-------------+
                     |  Services   |
                     +------+------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
       +-------------+             +-------------+
       |   Scanners  |             | PostgreSQL  |
       +------+------+             +-------------+
              |
       +------+------+
       |             |
       v             v
+-------------+ +-------------+
| SNMP Scanner| | WINK Scanner|
| asyncio     | | subprocess  |
+-------------+ +-------------+
                      |
                      v
              wink-rtsp-stats.exe
```

Monitoring Worker использует те же сервисы и сканеры, что и Web/API, где это необходимо.

**PostgreSQL является единственным источником истины для текущего состояния и истории мониторинга.**

---

# 3. Структура приложения

Целевая структура проекта:

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
│   │   ├── rtsp_client.py
│   │   └── wink.py
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
│   └── web/
│       ├── templates/
│       └── static/
│
├── migrations/
├── tests/
├── config/
├── systemd/
├── scripts/
├── docs/
│   ├── DATABASE_SCHEMA.md
│   └── ARCHITECTURE.md
│
├── pyproject.toml
├── README.md
└── TODO.md
```

Каждый модуль должен иметь одну основную ответственность.

---

# 4. FastAPI

FastAPI является HTTP/API-слоем приложения.

Он отвечает за:

* HTTP-маршрутизацию;
* валидацию входящих запросов;
* сериализацию ответов;
* обработку HTTP-ошибок;
* предоставление Web UI;
* health endpoints;
* вызов application services.

FastAPI **не должен содержать**:

* SNMP protocol logic;
* WINK subprocess logic;
* прямые SQL-запросы в route handlers;
* бизнес-правила мониторинга.

API вызывает сервисы.

```text
HTTP request
    |
    v
api/cameras.py
    |
    v
camera_service.py
    |
    v
SQLAlchemy
    |
    v
PostgreSQL
```

Для операций мониторинга:

```text
HTTP request
    |
    v
api/monitoring.py
    |
    v
monitoring_service.py
    |
    +--> snmp_service.py
    |        |
    |        v
    |   snmp_scanner.py
    |
    +--> wink_service.py
             |
             v
        wink_scanner.py
```

---

# 5. API

Предполагаемый набор API endpoints:

```text
GET    /api/cameras
POST   /api/cameras
GET    /api/cameras/{id}
PUT    /api/cameras/{id}
DELETE /api/cameras/{id}

POST   /api/cameras/{id}/test-snmp
POST   /api/cameras/{id}/test-rtsp

GET    /api/monitoring/summary
GET    /api/cameras/{id}/status

GET    /api/cameras/{id}/snmp
GET    /api/cameras/{id}/wink

GET    /api/cameras/{id}/history/snmp
GET    /api/cameras/{id}/history/wink

GET    /api/problems

GET    /health
GET    /health/ready
```

Конкретный список endpoints может изменяться во время реализации.

Route handlers при этом должны оставаться максимально тонкими.

---

# 6. Services

Слой `services` содержит application logic и business logic.

Сервисы координируют:

* database models;
* scanners;
* бизнес-правила;
* сохранение результатов.

## 6.1 camera_service.py

Отвечает за:

* создание камер;
* изменение камер;
* отключение камер;
* получение камер;
* импорт камер;
* экспорт камер;
* управление конфигурацией камер.

`camera_service.py` не должен реализовывать SNMP-протокол.

---

## 6.2 snmp_service.py

Отвечает за:

* подготовку SNMP-мониторинга;
* получение конфигурации и credentials камеры;
* вызов SNMP scanner;
* обработку результата scanner;
* расчёт SNMP status;
* сохранение SNMP measurement;
* сохранение подключённых RTSP clients.

---

## 6.3 wink_service.py

Отвечает за:

* подготовку WINK monitoring;
* получение RTSP credentials;
* вызов WINK scanner;
* обработку WINK JSON;
* расчёт WINK status;
* сохранение WINK measurement;
* сохранение WINK streams.

---

## 6.4 monitoring_service.py

Отвечает за orchestration.

Основной поток:

```text
Camera
   |
   +--> SNMP
   |
   +--> WINK
   |
   v
overall camera status
```

Сервис должен предоставлять операции:

* мониторинг одной камеры;
* мониторинг всех включённых камер;
* запуск SNMP monitoring;
* запуск WINK monitoring;
* получение текущего статуса;
* получение monitoring summary;
* получение списка проблем.

---

# 7. Scanners

`scanners` являются infrastructure adapters.

Они непосредственно взаимодействуют с внешними системами и возвращают структурированные Python-данные.

Scanner:

* не работает с Web UI;
* не содержит HTTP API;
* не должен напрямую записывать данные в PostgreSQL.

Архитектурный поток:

```text
Scanner
    |
    v
structured measurement
    |
    v
Service
    |
    v
business rules
    |
    v
SQLAlchemy
    |
    v
PostgreSQL
```

Это позволяет тестировать scanner независимо от базы данных.

---

# 8. SNMP Scanner

SNMP должен быть реализован через **чистый asyncio**.

Старая архитектура:

```text
ThreadPoolExecutor
    |
    v
worker thread
    |
    v
asyncio.run(...)
    |
    v
PySNMP
```

заменяется на:

```text
asyncio event loop
        |
        +-- SNMP camera 1
        +-- SNMP camera 2
        +-- SNMP camera 3
        +-- ...
        |
        +-- asyncio.Semaphore
```

SNMP scanner не должен создавать отдельный thread на каждую камеру.

---

# 9. SNMP concurrency

Количество одновременно выполняемых SNMP операций контролируется через `asyncio.Semaphore`.

Концептуально:

```python
semaphore = asyncio.Semaphore(SNMP_CONCURRENCY)


async def scan_camera(camera):
    async with semaphore:
        return await scan_snmp(camera)
```

Количество одновременных операций является конфигурационным параметром.

Вместо старого:

```text
MAX_THREADS
```

используется:

```text
SNMP_CONCURRENCY
```

Это отражает реальную модель выполнения.

`ThreadPoolExecutor` для SNMP больше не используется.

---

# 10. SNMP timeout и retries

Каждая SNMP операция должна иметь явно заданные:

* timeout;
* retry count;
* concurrency limit;
* exception handling.

Ошибка одной камеры не должна останавливать весь monitoring cycle.

Например:

```text
camera A -> success
camera B -> timeout
camera C -> success
camera D -> SNMP error
```

В этом случае:

* A обрабатывается нормально;
* B получает timeout/error status;
* C обрабатывается нормально;
* D получает error status.

Worker продолжает работу.

Ошибочные измерения не должны молча удаляться.

---

# 11. SNMP data flow

```text
Camera configuration
        |
        v
snmp_service
        |
        v
snmp_scanner
        |
        v
PySNMP
        |
        v
structured SNMP result
        |
        v
snmp_service
        |
        +--> calculate status
        |
        +--> save measurement
        |
        +--> save RTSP clients
        |
        v
PostgreSQL
```

SNMP scanner должен сохранять существующий набор полезных данных проекта:

* system information;
* IP counters;
* ICMP counters;
* MAC addresses;
* interface speed;
* active RTSP sessions;
* connected clients;
* timestamp;
* данные камеры.

---

# 12. WINK Scanner

WINK отличается от SNMP.

`wink-rtsp-stats.exe` является внешней программой и выполняет blocking operation.

Поэтому WINK не требуется искусственно превращать в pure asyncio protocol implementation.

Целевая архитектура:

```text
asyncio worker/service
        |
        v
bounded external process execution
        |
        v
wink-rtsp-stats.exe
        |
        v
JSON result
        |
        v
wink_service
        |
        v
PostgreSQL
```

Количество одновременно запущенных процессов должно быть ограничено.

---

# 13. WINK concurrency

WINK concurrency не связана с SNMP concurrency.

Например:

```text
WINK_CONCURRENCY=4
```

означает максимум четыре одновременно работающих процесса WINK.

Правило:

```text
SNMP
    -> asyncio concurrency

WINK
    -> bounded external-process concurrency
```

Это разные механизмы и разные настройки.

---

# 14. WINK process execution

WINK scanner должен обрабатывать:

* отсутствие executable;
* ошибку запуска процесса;
* timeout;
* ненулевой exit code;
* invalid JSON;
* неполный JSON;
* неизвестную схему JSON;
* ошибку подключения камеры.

Ошибка одного WINK процесса не должна завершать worker.

Пример:

```text
camera A -> WINK success
camera B -> timeout
camera C -> executable error
camera D -> valid result
```

A и D сохраняются нормально.

B и C получают соответствующий error/status.

---

# 15. WINK result processing

WINK scanner возвращает структурированный результат.

Service преобразует его в:

```text
wink_measurement
        |
        +--> wink_streams
```

Необходимо сохранять все полезные данные WINK.

В частности, где они присутствуют:

* duration;
* RTSP connect timing;
* first RTP timing;
* streams detected;
* bitrate;
* packet counts;
* packet loss;
* SSRC stability;
* transport mode;
* RTCP status;
* codec;
* payload type;
* clock rate;
* jitter;
* out-of-order packets;
* duplicated packets;
* burst metrics;
* clock drift;
* fingerprint.

Результат не должен быть упрощён только до:

```text
bitrate
loss
jitter
```

---

# 16. PostgreSQL

PostgreSQL является постоянным источником данных приложения.

Доступ к PostgreSQL выполняется через SQLAlchemy.

```text
FastAPI / Worker
       |
       v
Services
       |
       v
SQLAlchemy
       |
       v
PostgreSQL
```

Полная схема базы данных описывается отдельно:

```text
docs/DATABASE_SCHEMA.md
```

Изменения структуры БД выполняются через Alembic migrations.

---

# 17. Database access rules

API routes и scanners не должны содержать произвольные SQL-запросы.

Доступ к базе должен находиться в соответствующем application/data-access слое.

Scanner не должен знать о существовании PostgreSQL.

Неправильно:

```text
snmp_scanner
    |
    +--> PostgreSQL
```

Правильно:

```text
snmp_scanner
    |
    v
snmp_service
    |
    v
SQLAlchemy
    |
    v
PostgreSQL
```

Это позволяет тестировать scanner отдельно.

---

# 18. Web и Worker

Приложение разделяется на два самостоятельных long-running процесса.

## Web process

Отвечает за:

* FastAPI;
* REST API;
* Web UI;
* управление камерами;
* просмотр истории;
* текущие статусы;
* ручной запуск monitoring operations.

Web process не должен постоянно сканировать все камеры.

## Worker process

Отвечает за:

* scheduled monitoring;
* SNMP scans;
* WINK scans;
* сохранение результатов;
* расчёт статусов;
* logging monitoring cycles.

Архитектура:

```text
                  PostgreSQL
                 /          \
                /            \
               v              v
        Web process       Worker process
             |                  |
          FastAPI          monitoring_service
             |                  |
             v                  v
           Browser          scanners
```

---

# 19. Worker loop

Worker периодически выполняет monitoring cycle:

```text
start
  |
  v
load enabled cameras
  |
  v
run monitoring
  |
  +--> SNMP
  |
  +--> WINK
  |
  v
persist results
  |
  v
calculate current status
  |
  v
wait for next interval
  |
  +---------> repeat
```

Worker не должен зависеть от текущего working directory.

---

# 20. Worker failure isolation

Ошибка одной камеры не должна останавливать Worker.

SNMP timeout не должен останавливать WINK.

WINK failure не должен останавливать SNMP.

Повреждённый результат одной камеры не должен уничтожать результаты других камер.

Ошибки должны обрабатываться на соответствующих границах и сохраняться в диагностической информации.

---

# 21. Manual monitoring

Web UI может предоставлять:

```text
Test SNMP
Test RTSP/WINK
Run monitoring now
```

Эти операции должны использовать те же services, которые использует scheduled Worker.

Например:

```text
POST /api/cameras/{id}/test-snmp
        |
        v
    snmp_service
        |
        v
    snmp_scanner
```

Это предотвращает появление двух разных реализаций мониторинга:

```text
Web implementation
Worker implementation
```

---

# 22. Current status и history

PostgreSQL хранит историю измерений.

Web UI показывает актуальное состояние на основании последних измерений.

```text
Historical measurements
        |
        +--> latest SNMP measurement
        |
        +--> latest WINK measurement
        |
        v
overall camera status
        |
        v
Dashboard
```

History endpoints читают исторические measurements непосредственно из PostgreSQL.

---

# 23. Unified camera status

Отдельная таблица текущих статусов не требуется.

Статус камеры определяется на основании последних результатов мониторинга.

```text
SNMP status
WINK status
     |
     v
overall status
```

Предусматриваются состояния:

```text
ONLINE
WARNING
ERROR
OFFLINE
DISABLED
UNKNOWN
```

Приоритеты статусов реализуются в:

```text
app/services/monitoring_service.py
```

---

# 24. Configuration

Конфигурация приложения находится в:

```text
app/config.py
```

Настраиваемые параметры включают:

* PostgreSQL connection;
* SNMP port;
* SNMP timeout;
* SNMP retries;
* SNMP concurrency;
* WINK executable path;
* WINK concurrency;
* monitoring interval;
* application host;
* application port;
* logging level;
* runtime directories.

Secrets не должны быть hardcoded в Python source code.

---

# 25. Runtime paths

Приложение не должно зависеть от директории, из которой оно запущено.

Следующие конструкции не должны быть обязательным runtime storage:

```text
./scanned_metrics
./metrics_json
./report-snmp.html
./report-wink.html
```

Runtime paths должны задаваться конфигурацией.

После перехода на PostgreSQL JSON-файлы больше не являются основным хранилищем мониторинга.

---

# 26. JSON и Excel после миграции

JSON становится дополнительным форматом для:

* debug;
* export;
* migration;
* диагностики.

Worker не должен зависеть от JSON-файлов для определения текущего состояния.

Модель:

```text
PostgreSQL
    = primary storage

JSON
    = optional diagnostic/export format

cameras.xlsx
    = import/export format
```

Excel используется для импорта/экспорта данных камер.

Runtime database — PostgreSQL.

---

# 27. Dependency boundaries

Целевое направление зависимостей:

```text
API
 |
 v
Services
 |
 +--> Models / database
 |
 +--> Scanners
```

Правила:

```text
Scanners
    X--> API

Models
    X--> Scanners

Configuration
    X--> business logic
```

Это предотвращает circular dependencies и позволяет независимо тестировать компоненты.

---

# 28. Testing architecture

Тесты должны быть разделены по ответственности.

Целевая структура:

```text
tests/
|
+-- test_camera_service.py
+-- test_snmp_service.py
+-- test_wink_service.py
+-- test_monitoring_service.py
+-- test_snmp_scanner.py
+-- test_wink_scanner.py
+-- test_api_cameras.py
+-- test_api_monitoring.py
```

SNMP scanner tests используют mock SNMP transport.

WINK scanner tests используют mock external process.

Service tests проверяют:

* business rules;
* обработку ошибок;
* persistence behavior.

API tests проверяют HTTP contracts.

---

# 29. systemd deployment

Целевая deployment-модель использует два systemd service:

```text
systemd
   |
   +-- monitoring-rsvn-web.service
   |
   +-- monitoring-rsvn-worker.service
```

## monitoring-rsvn-web.service

Запускает FastAPI/Uvicorn.

## monitoring-rsvn-worker.service

Запускает monitoring worker.

Оба процесса используют один application package и одну конфигурацию.

---

# 30. Web service lifecycle

Целевой lifecycle:

```text
systemd
   |
   v
Uvicorn
   |
   v
FastAPI
   |
   v
PostgreSQL
```

Web service должен предоставлять health endpoints для контроля состояния процесса.

---

# 31. Worker service lifecycle

Целевой lifecycle:

```text
systemd
   |
   v
worker entry point
   |
   v
monitoring_service
   |
   +--> SNMP
   |
   +--> WINK
   |
   v
PostgreSQL
```

Worker должен завершаться с ненулевым exit code только при unrecoverable application/infrastructure failure.

Ошибка отдельной камеры является recoverable error.

---

# 32. Logging

Логирование централизовано.

Используется стандартный Python `logging`.

Разрозненные `print()` не используются как основной механизм logging.

Логи должны содержать:

* timestamp;
* level;
* component;
* camera identifier, если применимо;
* operation;
* error details.

Пароли и другие sensitive credentials никогда не должны попадать в logs.

Допустимо записывать:

```text
Camera 535: SNMP scan started
Camera 535: SNMP scan completed
```

Недопустимо:

```text
Camera 535 password: ...
RTSP URL: rtsp://user:password@...
```

---

# 33. Security boundary

Пароли камер **не удаляются**.

Они необходимы системе для выполнения мониторинга.

Однако credentials должны быть отделены от общей информации о камере.

Правила:

* credentials хранятся отдельно от общей metadata камеры;
* password не отображается в обычном Dashboard;
* password не записывается в logs;
* credentials не включаются в обычные monitoring summaries;
* API возвращает credentials только через явно предназначенные для этого административные операции.

Важно:

**сохранение паролей является обязательным требованием архитектуры.**

---

# 34. Architectural rules

Следующие правила являются обязательными для целевой реализации.

1. PostgreSQL является source of truth.
2. SQLAlchemy используется для database access.
3. Alembic используется для database migrations.
4. FastAPI является HTTP/API layer.
5. Business logic находится в services.
6. Внешние monitoring protocols/processes находятся в scanners.
7. SNMP использует pure asyncio.
8. SNMP concurrency контролируется через asyncio semaphore.
9. SNMP не использует старую модель ThreadPoolExecutor/`MAX_THREADS`.
10. WINK использует bounded external-process concurrency.
11. Ошибка WINK executable изолируется на уровне отдельной камеры.
12. Ошибка одной камеры не должна останавливать monitoring cycle.
13. Web и Worker являются отдельными процессами.
14. Web и Worker используют общие services.
15. Runtime monitoring state не хранится в JSON.
16. Excel используется для import/export, а не как runtime database.
17. Пароли камер сохраняются.
18. Пароли не появляются в обычных logs и dashboards.
19. Runtime paths являются конфигурационными параметрами.
20. Существующие SNMP/WINK business rules сохраняются, если явно не принято решение их изменить.

---

# 35. Итоговая модель

```text
                         Browser
                            |
                            v
                     +-------------+
                     |   FastAPI   |
                     |     Web     |
                     +------+------+
                            |
                            v
                     +-------------+
                     |  Services   |
                     +------+------+
                            |
                    +-------+-------+
                    |               |
                    v               v
               PostgreSQL       Scanners
                                   |
                         +---------+---------+
                         |                   |
                         v                   v
                  Async SNMP          WINK process
                  + semaphore         + bounded concurrency
                         |                   |
                         v                   v
                      Cameras             Cameras


                    Separate Worker
                          |
                          v
                 monitoring_service
                          |
                   +------+------+
                   |             |
                   v             v
                 SNMP           WINK
                   |             |
                   +------+------+
                          |
                          v
                     PostgreSQL
```

Эта архитектура является базовой архитектурой для дальнейшей реализации проекта.

Изменения, затрагивающие:

* границы процессов;
* ответственность PostgreSQL;
* структуру scanners;
* стратегию concurrency;
* работу с credentials;

должны быть сначала отражены в документации и только после этого реализованы в коде.
