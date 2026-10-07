# Monitoring RSVN — TODO.md

> Дорожная карта разработки и архитектурной переработки проекта `monitoring-rsvn`.
>
> Документ является рабочей точкой продолжения разработки.
> После каждого значимого этапа статус задач должен обновляться здесь.
>
> Последнее актуальное состояние репозитория: `main`, 2026-10-07.

---

## Статусы

* `[ ]` — не выполнено
* `[~]` — выполняется
* `[x]` — выполнено
* `[!]` — блокирующий вопрос / требуется решение
* `[?]` — требуется дополнительное исследование

## Ответственные

* `AI` — выполняет ИИ-агент
* `DEV` — действие или решение разработчика
* `AI+DEV` — совместная работа

---

# 0. Главная цель проекта

Перевести исходный скриптовый мониторинг SNMP/WINK на полноценное модульное приложение:

```text
                    Browser
                       |
                       v
                 FastAPI / Web UI
                       |
                       v
                   Services
                  /        \
                 /          \
                v            v
             SNMP           WINK
            Scanner        Scanner
                \            /
                 \          /
                    PostgreSQL
```

Целевое приложение должно:

* хранить конфигурацию камер в PostgreSQL;
* хранить credentials камер;
* выполнять SNMP-мониторинг;
* выполнять WINK/RTSP-мониторинг;
* хранить историю измерений;
* предоставлять API;
* предоставлять Web UI;
* позволять управлять камерами;
* предоставлять историю и диагностику;
* запускаться как отдельные `web` и `worker` процессы;
* не зависеть от JSON-файлов как от основного runtime-хранилища.

---

# 1. Исходный проект

Изначально проект состоял из четырёх основных скриптов:

```text
scan-snmp.py
scan-wink.py
generate-snmp-report.py
generate-wink-report.py
```

Старая архитектура:

```text
cameras.xlsx
      |
      +--------------------+
      |                    |
      v                    v
scan-snmp.py          scan-wink.py
      |                    |
      v                    v
SNMP JSON              WINK JSON
      |                    |
      v                    v
generate-*            generate-*
      |                    |
      v                    v
HTML reports
```

Старые скрипты пока **не удаляются**.

Они остаются до завершения новой реализации, миграции данных и regression testing.

---

# 2. Фактическое состояние репозитория

На текущий момент в репозитории существуют:

```text
TODO.md
pyproject.toml
alembic.ini

app/
├── config.py
├── database.py
└── models/
    ├── __init__.py
    ├── camera.py
    ├── credentials.py
    ├── rtsp_client.py
    ├── snmp_measurement.py
    ├── wink_measurement.py
    └── wink_stream.py

docs/
├── ARCHITECTURE.md
└── DATABASE_SCHEMA.md

migrations/
├── env.py
├── script.py.mako
└── versions/
    └── 0001_initial_schema.py

scan-snmp.py
scan-wink.py
generate-snmp-report.py
generate-wink-report.py
```

Пока отсутствуют:

```text
app/__init__.py
app/main.py
app/worker.py

app/scanners/
app/services/
app/schemas/
app/api/
app/web/

tests/
systemd/
config/

README.md
```

---

# 3. Что уже сделано

## 3.1 Архитектурное проектирование

* [x] `AI` Проведён аудит исходной архитектуры.
* [x] `AI` Определено разделение Web/API, services, scanners и database.
* [x] `AI` Определено разделение Web process и Monitoring Worker.
* [x] `AI` Определена PostgreSQL как основная СУБД.
* [x] `AI` Определено, что PostgreSQL является source of truth.
* [x] `AI` Определено, что JSON больше не является основной БД.
* [x] `AI` Определена целевая модульная структура проекта.

Документ:

```text
docs/ARCHITECTURE.md
```

---

## 3.2 PostgreSQL schema

* [x] `AI` Определена схема PostgreSQL.
* [x] `AI` Определена таблица `cameras`.
* [x] `AI` Определена таблица `camera_credentials`.
* [x] `AI` Определена таблица `snmp_measurements`.
* [x] `AI` Определена таблица `rtsp_clients`.
* [x] `AI` Определена таблица `wink_measurements`.
* [x] `AI` Определена таблица `wink_streams`.
* [x] `AI` Определены foreign keys.
* [x] `AI` Определены основные indexes.
* [x] `AI` Определены unique constraints.
* [x] `AI` Определена стратегия хранения истории.
* [x] `AI` Определена стратегия хранения timestamps.
* [x] `AI` Определено соответствие старых SNMP JSON новым таблицам.
* [x] `AI` Определено соответствие старых WINK JSON новым таблицам.
* [x] `AI` Зафиксированы данные WINK, которые нельзя потерять.

Документ:

```text
docs/DATABASE_SCHEMA.md
```

---

## 3.3 Python dependencies

* [x] `AI` Создан `pyproject.toml`.
* [x] `AI` Добавлен FastAPI.
* [x] `AI` Добавлен Uvicorn.
* [x] `AI` Добавлен Pydantic.
* [x] `AI` Добавлен pydantic-settings.
* [x] `AI` Добавлен SQLAlchemy 2.x.
* [x] `AI` Добавлен asyncpg.
* [x] `AI` Добавлен Alembic.
* [x] `AI` Добавлен PySNMP 7.x.
* [x] `AI` Добавлен openpyxl.
* [x] `AI` Добавлен Jinja2.
* [x] `AI` Добавлены pytest и pytest-asyncio.
* [x] `AI` Добавлен httpx.
* [x] `AI` Добавлен Ruff.
* [x] `AI` Настроен pytest.
* [x] `AI` Настроен Ruff.
* [x] `AI` Настроены entry points:

```text
monitoring-rsvn-web
monitoring-rsvn-worker
```

---

# 4. Application configuration

Создан:

```text
app/config.py
```

Выполнено:

* [x] `AI` Создан централизованный объект `Settings`.
* [x] `AI` Используется `pydantic-settings`.
* [x] `AI` Поддерживается `.env`.
* [x] `AI` Конфигурация приложения вынесена из бизнес-кода.
* [x] `AI` Настроены host/port.
* [x] `AI` Настроен log level.
* [x] `AI` Настроен `database_url`.
* [x] `AI` Настроены database pool settings.
* [x] `AI` Настроены runtime directories.
* [x] `AI` Настроен путь к `cameras.xlsx`.
* [x] `AI` Настроены SNMP timeout/retries.
* [x] `AI` Настроен SNMP concurrency.
* [x] `AI` Настроен путь к `wink-rtsp-stats.exe`.
* [x] `AI` Настроен WINK concurrency.
* [x] `AI` Настроен WINK timeout.
* [x] `AI` Настроен monitoring interval.
* [x] `AI` Настроены monitoring retries.
* [x] `AI` Вынесены сетевые фильтры.
* [x] `AI` Добавлен флаг `log_sensitive_urls`.
* [x] `AI` Реализован cached `get_settings()`.

---

# 5. Database infrastructure

Создан:

```text
app/database.py
```

Выполнено:

* [x] `AI` Создан SQLAlchemy `DeclarativeBase`.
* [x] `AI` Создана naming convention для PostgreSQL/Alembic.
* [x] `AI` Создан async SQLAlchemy engine.
* [x] `AI` Используется asyncpg.
* [x] `AI` Создан `AsyncSessionFactory`.
* [x] `AI` Создан `get_db_session()`.
* [x] `AI` Создана проверка соединения с PostgreSQL.
* [x] `AI` Добавлено корректное закрытие database engine.
* [x] `AI` Добавлен безопасный `get_engine_info()`.
* [x] `AI` Database credentials не выводятся через `get_engine_info()`.

Важно:

```text
app/database.py
```

является инфраструктурным слоем и не содержит бизнес-логики мониторинга.

---

# 6. ORM models

## 6.1 Структура

Фактически создана:

```text
app/models/
├── __init__.py
├── camera.py
├── credentials.py
├── rtsp_client.py
├── snmp_measurement.py
├── wink_measurement.py
└── wink_stream.py
```

Выполнено:

* [x] `AI` Создан `app/models/__init__.py`.
* [x] `AI` Создан `Camera`.
* [x] `AI` Создан `CameraCredential`.
* [x] `AI` Создан `SnmpMeasurement`.
* [x] `AI` Создан `RtspClient`.
* [x] `AI` Создан `WinkMeasurement`.
* [x] `AI` Создан `WinkStream`.
* [x] `AI` Все модели подключены к `Base`.
* [x] `AI` Определены relationships.
* [x] `AI` Определены foreign keys.
* [x] `AI` Определены cascade relationships.
* [x] `AI` Определены indexes.
* [x] `AI` Определены unique constraints.
* [x] `AI` Определены nullable/non-nullable поля.
* [x] `AI` Используются timezone-aware datetime.
* [x] `AI` `Base.metadata.create_all()` не используется как production migration mechanism.

### Важное соответствие

Текущая реализация использует:

```text
app/models/snmp_measurement.py
app/models/wink_measurement.py
```

а не старые плановые имена:

```text
snmp.py
wink.py
```

Дальнейший TODO должен соответствовать фактической структуре репозитория.

---

# 7. Alembic

## 7.1 Migration infrastructure

Фактически создано:

```text
alembic.ini

migrations/
├── env.py
├── script.py.mako
└── versions/
```

Выполнено:

* [x] `AI` Создан `alembic.ini`.
* [x] `AI` Создана корневая директория `migrations/`.
* [x] `AI` Создан `migrations/env.py`.
* [x] `AI` Настроен async SQLAlchemy/Alembic.
* [x] `AI` Подключена metadata всех ORM-моделей.
* [x] `AI` Database URL получается через application settings.
* [x] `AI` Database password не хранится в migration files.
* [x] `AI` Поддерживается offline migration mode.
* [x] `AI` Поддерживается online migration mode.

---

## 7.2 Initial migration

Создано:

```text
migrations/versions/0001_initial_schema.py
```

Выполнено:

* [x] `AI` Создана initial migration.
* [x] `AI` Создаётся `cameras`.
* [x] `AI` Создаётся `camera_credentials`.
* [x] `AI` Создаётся `snmp_measurements`.
* [x] `AI` Создаётся `rtsp_clients`.
* [x] `AI` Создаётся `wink_measurements`.
* [x] `AI` Создаётся `wink_streams`.
* [x] `AI` Создаются foreign keys.
* [x] `AI` Создаются основные indexes.
* [x] `AI` Создаются unique constraints.
* [x] `AI` Реализован downgrade.

### Осталось проверить реально на PostgreSQL

* [ ] `AI+DEV` Выполнить `alembic upgrade head`.
* [ ] `AI+DEV` Проверить фактическое создание всех таблиц.
* [ ] `AI+DEV` Выполнить `alembic downgrade base`.
* [ ] `AI+DEV` Повторно выполнить `alembic upgrade head`.
* [ ] `AI+DEV` Проверить migration chain на реальной PostgreSQL.
* [ ] `AI` Проверить `alembic check`.
* [ ] `AI` Проверить отсутствие расхождений ORM metadata и migration state.

---

# 8. Application package

Это **текущий ближайший этап разработки**.

`pyproject.toml` уже содержит:

```text
monitoring-rsvn-web = "app.main:main"
monitoring-rsvn-worker = "app.worker:main"
```

Но соответствующие модули ещё не созданы.

Создать:

```text
app/
├── __init__.py
├── main.py
└── worker.py
```

Задачи:

* [ ] `AI` Создать `app/__init__.py`.
* [ ] `AI` Создать `app/main.py`.
* [ ] `AI` Создать `app/worker.py`.
* [ ] `AI` Реализовать минимальную точку входа Web.
* [ ] `AI` Реализовать минимальную точку входа Worker.
* [ ] `AI` Не помещать бизнес-логику в entry point.
* [ ] `AI` Проверить импорт `app.main`.
* [ ] `AI` Проверить импорт `app.worker`.
* [ ] `AI` Проверить:

```bash
python -m app.main
```

* [ ] `AI` Проверить:

```bash
monitoring-rsvn-web
```

* [ ] `AI` Проверить:

```bash
monitoring-rsvn-worker
```

---

# 9. Logging

Создать:

```text
app/logging_config.py
```

Задачи:

* [ ] `AI` Создать централизованную logging configuration.
* [ ] `AI` Настроить console logging.
* [ ] `AI` Настроить file logging при необходимости.
* [ ] `AI` Настроить log level через settings.
* [ ] `AI` Добавить timestamps.
* [ ] `AI` Добавить module/logger names.
* [ ] `AI` Не писать passwords в лог.
* [ ] `AI` Не писать полный RTSP URL с credentials.
* [ ] `AI` Не логировать database password.
* [ ] `AI` Логировать ошибки SNMP.
* [ ] `AI` Логировать ошибки WINK.
* [ ] `AI` Логировать начало и окончание monitoring cycle.
* [ ] `AI` Убрать использование `print()` как основного logging mechanism.

---

# 10. SNMP scanner

Создать:

```text
app/scanners/
├── __init__.py
└── snmp_scanner.py
```

Целевая модель:

```text
asyncio event loop
        |
        +--> camera #1
        +--> camera #2
        +--> camera #3
        +--> ...
        |
asyncio.Semaphore(snmp_concurrency)
```

Задачи:

* [ ] `AI` Создать `app/scanners/`.
* [ ] `AI` Создать `app/scanners/__init__.py`.
* [ ] `AI` Создать `app/scanners/snmp_scanner.py`.
* [ ] `AI` Перенести SNMP protocol logic.
* [ ] `AI` Удалить `ThreadPoolExecutor` из новой реализации.
* [ ] `AI` Не использовать `asyncio.run()` для каждой камеры.
* [ ] `AI` Использовать единый event loop.
* [ ] `AI` Использовать `asyncio.Semaphore`.
* [ ] `AI` Перенести SNMP timeout.
* [ ] `AI` Перенести retries.
* [ ] `AI` Проверить PySNMP 7.x API.
* [ ] `AI` Реализовать SNMP GET.
* [ ] `AI` Реализовать SNMP WALK.
* [ ] `AI` Реализовать TCP table walk.
* [ ] `AI` Обработать timeout.
* [ ] `AI` Обработать SNMP error status.
* [ ] `AI` Обработать недоступную камеру.
* [ ] `AI` Убрать silent `except Exception: pass`.
* [ ] `AI` Возвращать structured Python result.
* [ ] `AI` Не позволять scanner напрямую записывать данные в БД.

---

# 11. SNMP data collection

Новый scanner должен сохранять полезный набор данных старого проекта:

* system information;
* IP counters;
* ICMP counters;
* MAC addresses;
* interface speed;
* active RTSP sessions;
* connected clients;
* timestamp;
* camera information.

Data flow:

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

---

# 12. SNMP service

Создать:

```text
app/services/
├── __init__.py
└── snmp_service.py
```

Задачи:

* [ ] `AI` Получать camera configuration.
* [ ] `AI` Получать SNMP credentials.
* [ ] `AI` Вызывать `snmp_scanner`.
* [ ] `AI` Преобразовывать scanner result в domain measurement.
* [ ] `AI` Рассчитывать SNMP status.
* [ ] `AI` Сохранять `snmp_measurements`.
* [ ] `AI` Сохранять `rtsp_clients`.
* [ ] `AI` Сохранять timestamp.
* [ ] `AI` Сохранять ошибки измерения.
* [ ] `AI` Не смешивать scanner и database logic.

---

# 13. SNMP status

Существующие бизнес-правила должны быть сохранены.

Например:

```text
uptime < 1 дня
    → нарушение

interface_speed < 100 Mbps
    → нарушение
```

Задачи:

* [ ] `AI` Формализовать SNMP status.
* [ ] `AI` Определить enum/constants.
* [ ] `AI` Зафиксировать порядок проверок.
* [ ] `AI` Написать unit tests.
* [ ] `AI` Проверить пограничные значения.
* [ ] `AI` Не изменять исходные измеренные значения при расчёте статуса.

---

# 14. WINK / RTSP scanner

Создать:

```text
app/scanners/wink_scanner.py
```

WINK использует внешний процесс:

```text
wink-rtsp-stats.exe
```

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

Задачи:

* [ ] `AI` Создать `wink_scanner.py`.
* [ ] `AI` Перенести запуск `wink-rtsp-stats.exe`.
* [ ] `AI` Перенести subprocess logic.
* [ ] `AI` Использовать настроенный executable path.
* [ ] `AI` Использовать `wink_concurrency`.
* [ ] `AI` Реализовать timeout.
* [ ] `AI` Обработать отсутствие executable.
* [ ] `AI` Обработать ошибку запуска процесса.
* [ ] `AI` Обработать ненулевой exit code.
* [ ] `AI` Обработать invalid JSON.
* [ ] `AI` Обработать пустой результат.
* [ ] `AI` Обработать неизвестную схему JSON.
* [ ] `AI` Возвращать structured Python result.
* [ ] `AI` Не записывать данные непосредственно в БД.

---

# 15. WINK concurrency

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

Задачи:

* [ ] `AI` Реализовать отдельный WINK semaphore/limiter.
* [ ] `AI` Проверить, что WINK process limit соблюдается.
* [ ] `AI` Проверить timeout cleanup.
* [ ] `AI` Проверить корректное завершение subprocess.
* [ ] `AI` Проверить отсутствие orphan processes.

---

# 16. WINK service

Создать:

```text
app/services/wink_service.py
```

Задачи:

* [ ] `AI` Получать credentials камеры.
* [ ] `AI` Формировать runtime WINK request.
* [ ] `AI` Вызывать WINK scanner.
* [ ] `AI` Разбирать WINK result.
* [ ] `AI` Сохранять `wink_measurements`.
* [ ] `AI` Сохранять `wink_streams`.
* [ ] `AI` Рассчитывать packet loss.
* [ ] `AI` Рассчитывать bitrate.
* [ ] `AI` Рассчитывать jitter.
* [ ] `AI` Рассчитывать итоговый status.
* [ ] `AI` Сохранять ошибки.
* [ ] `AI` При необходимости сохранять raw result.

---

# 17. WINK result data

Необходимо сохранять все полезные данные WINK.

В частности:

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

# 18. WINK status

Сохранить существующий порядок правил:

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

Задачи:

* [ ] `AI` Формализовать порядок проверок.
* [ ] `AI` Вынести thresholds в configuration.
* [ ] `AI` Создать enum/constants.
* [ ] `AI` Написать unit tests.
* [ ] `AI` Проверить пограничные значения.
* [ ] `AI` Проверить несколько streams.
* [ ] `AI` Проверить отсутствие streams.
* [ ] `AI` Проверить деление на ноль/отсутствие packet counters.

---

# 19. Monitoring service

Создать:

```text
app/services/monitoring_service.py
```

Это orchestration layer.

Задачи:

* [ ] `AI` Создать orchestration layer.
* [ ] `AI` Реализовать мониторинг одной камеры.
* [ ] `AI` Реализовать мониторинг всех enabled камер.
* [ ] `AI` Запускать SNMP.
* [ ] `AI` Запускать WINK.
* [ ] `AI` Собирать результаты.
* [ ] `AI` Определять общий status камеры.
* [ ] `AI` Реализовать monitoring summary.
* [ ] `AI` Реализовать problems list.
* [ ] `AI` Не помещать orchestration logic в API routes.
* [ ] `AI` Изолировать ошибки отдельных камер.

---

# 20. Общий статус камеры

Предварительные статусы:

```text
DISABLED
OFFLINE
ERROR
WARNING
ONLINE
UNKNOWN
```

Задачи:

* [ ] `AI` Формализовать status priority.
* [ ] `AI` Определить влияние SNMP на общий status.
* [ ] `AI` Определить влияние WINK на общий status.
* [ ] `AI` Определить поведение при отсутствии одного из measurements.
* [ ] `AI` Реализовать единый алгоритм.
* [ ] `AI` Написать unit tests.
* [ ] `AI` Проверить все комбинации SNMP/WINK states.

---

# 21. Camera service / CRUD

Создать:

```text
app/services/camera_service.py
```

Задачи:

* [ ] `AI` Реализовать получение списка камер.
* [ ] `AI` Реализовать получение одной камеры.
* [ ] `AI` Реализовать создание камеры.
* [ ] `AI` Реализовать изменение камеры.
* [ ] `AI` Реализовать enable/disable.
* [ ] `AI` Реализовать административное удаление.
* [ ] `AI` Сохранять исторические measurements при обычном disable.
* [ ] `AI` Проверять уникальность camera number.
* [ ] `AI` Валидировать IP address.
* [ ] `AI` Валидировать обязательные поля.

---

# 22. Credentials

Критическое правило:

> Пароли камер и RTSP credentials не удаляются из рабочего процесса.

Задачи:

* [x] `AI` Реализована ORM-модель `CameraCredential`.
* [x] `AI` В модели предусмотрен username.
* [x] `AI` В модели предусмотрен password.
* [x] `AI` В модели предусмотрен SNMP community.
* [ ] `AI` Использовать credentials для WINK.
* [ ] `AI` Использовать SNMP community для SNMP.
* [ ] `AI` Не выводить password в обычных API responses.
* [ ] `AI` Не писать password в logs.
* [ ] `AI+DEV` Отдельно решить вопрос шифрования credentials.
* [ ] `AI` Не делать encryption блокером текущего этапа.

---

# 23. FastAPI application

Создать:

```text
app/main.py
```

Задачи:

* [ ] `AI` Создать FastAPI application.
* [ ] `AI` Создать application lifecycle.
* [ ] `AI` Подключить logging.
* [ ] `AI` Подключить database lifecycle.
* [ ] `AI` Подключить routers.
* [ ] `AI` Добавить `/health`.
* [ ] `AI` Добавить `/health/ready`.
* [ ] `AI` Проверять database readiness.
* [ ] `AI` Настроить graceful shutdown.
* [ ] `AI` Проверить OpenAPI.
* [ ] `AI` Не помещать бизнес-логику в route handlers.

---

# 24. Pydantic schemas

Создать:

```text
app/schemas/
├── __init__.py
├── camera.py
├── monitoring.py
├── history.py
└── common.py
```

Задачи:

* [ ] `AI` Создать request schemas.
* [ ] `AI` Создать response schemas.
* [ ] `AI` Создать camera schemas.
* [ ] `AI` Создать monitoring schemas.
* [ ] `AI` Создать history schemas.
* [ ] `AI` Скрыть credentials из обычных responses.
* [ ] `AI` Валидировать входные данные через Pydantic.
* [ ] `AI` Не возвращать ORM models напрямую наружу без контролируемой serialization boundary.

---

# 25. API package

Создать:

```text
app/api/
├── __init__.py
├── cameras.py
├── monitoring.py
├── history.py
└── health.py
```

Правило:

```text
API
 |
 v
Services
 |
 +--> Models / DB
 |
 +--> Scanners
```

API не должен содержать business logic.

---

# 26. API cameras

Задачи:

* [ ] `AI` Реализовать GET cameras.
* [ ] `AI` Реализовать POST camera.
* [ ] `AI` Реализовать GET camera.
* [ ] `AI` Реализовать PUT/PATCH camera.
* [ ] `AI` Реализовать DELETE camera.
* [ ] `AI` Реализовать enable/disable.
* [ ] `AI` Реализовать manual SNMP test.
* [ ] `AI` Реализовать manual RTSP test.
* [ ] `AI` Проверить validation errors.
* [ ] `AI` Проверить credentials exposure.

---

# 27. API monitoring

Задачи:

* [ ] `AI` Реализовать monitoring summary.
* [ ] `AI` Реализовать current camera status.
* [ ] `AI` Реализовать current SNMP state.
* [ ] `AI` Реализовать current WINK state.
* [ ] `AI` Реализовать problems endpoint.
* [ ] `AI` Добавить возможность ручного monitoring cycle.
* [ ] `AI` Использовать те же services, что и Worker.

---

# 28. API history

Задачи:

* [ ] `AI` Реализовать history SNMP.
* [ ] `AI` Реализовать history WINK.
* [ ] `AI` Добавить period filters.
* [ ] `AI` Добавить pagination.
* [ ] `AI` Добавить сортировку по timestamp.
* [ ] `AI` Не загружать неограниченное количество measurements одним запросом.
* [ ] `AI` Проверить индексы исторических запросов.
* [ ] `AI` Добавить фильтр по camera.

---

# 29. API health

Задачи:

* [ ] `AI` Реализовать `/health`.
* [ ] `AI` Реализовать `/health/ready`.
* [ ] `AI` Проверять PostgreSQL для readiness.
* [ ] `AI` Не считать HTTP 200 доказательством работоспособности мониторинга.
* [ ] `AI` При необходимости добавить worker status.

---

# 30. Monitoring worker

Создать:

```text
app/worker.py
```

Worker выполняет:

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

Задачи:

* [ ] `AI` Создать worker entry point.
* [ ] `AI` Реализовать monitoring loop.
* [ ] `AI` Использовать `monitoring_interval`.
* [ ] `AI` Использовать `monitoring_retries`.
* [ ] `AI` Корректно обрабатывать исключение одной камеры.
* [ ] `AI` Не останавливать весь worker из-за одной камеры.
* [ ] `AI` Реализовать graceful shutdown.
* [ ] `AI` Логировать начало/конец cycle.
* [ ] `AI` Проверить корректное завершение asyncio tasks.
* [ ] `AI` Не помещать SQL implementation details непосредственно в worker.
* [ ] `AI` Не помещать scanner implementation непосредственно в worker.

---

# 31. Worker failure isolation

Обязательные правила:

```text
SNMP timeout
    X--> остановка Worker

WINK failure
    X--> остановка SNMP

Camera A failure
    X--> потеря Camera B

Invalid WINK JSON
    X--> остановка monitoring cycle
```

Задачи:

* [ ] `AI` Проверить isolation на уровне камеры.
* [ ] `AI` Проверить isolation SNMP/WINK.
* [ ] `AI` Проверить recoverable/unrecoverable errors.
* [ ] `AI` Проверить cleanup после exceptions.

---

# 32. Excel import/export

Excel используется только как import/export format.

Создать:

```text
app/services/import_service.py
app/services/export_service.py
```

Задачи:

* [ ] `AI` Создать import service.
* [ ] `AI` Создать export service.
* [ ] `AI` Определить mapping старого XLSX.
* [ ] `AI` Валидировать XLSX.
* [ ] `AI` Не создавать дубликаты при повторном импорте.
* [ ] `AI` Корректно обновлять существующие камеры.
* [ ] `AI` Сохранять credentials.
* [ ] `AI` Добавить API import.
* [ ] `AI` Добавить API export.
* [ ] `AI` Убрать обязательную runtime-зависимость от XLSX.

---

# 33. Web UI

Целевая структура:

```text
app/web/
├── __init__.py
├── templates/
└── static/
```

Задачи:

* [ ] `AI` Создать базовый layout.
* [ ] `AI` Создать Dashboard.
* [ ] `AI` Создать список камер.
* [ ] `AI` Создать карточку камеры.
* [ ] `AI` Создать страницу истории.
* [ ] `AI` Создать страницу проблем.
* [ ] `AI` Создать управление камерой.
* [ ] `AI` Добавить SNMP status.
* [ ] `AI` Добавить WINK status.
* [ ] `AI` Добавить overall status.
* [ ] `AI` Добавить возможность просмотра credentials только через явное административное действие.
* [ ] `AI` Добавить ручной SNMP test.
* [ ] `AI` Добавить ручной RTSP test.
* [ ] `AI` Добавить графики истории.

---

# 34. Dashboard

Задачи:

* [ ] `AI` Реализовать summary endpoint.
* [ ] `AI` Реализовать dashboard.
* [ ] `AI` Реализовать получение последнего measurement эффективно.
* [ ] `AI` Не выполнять N+1 SQL queries.
* [ ] `AI` Проверить производительность Dashboard.
* [ ] `AI` Отображать количество ONLINE/WARNING/ERROR/OFFLINE.
* [ ] `AI` Отображать список проблемных камер.

---

# 35. History

Задачи:

* [ ] `AI` Реализовать historical queries.
* [ ] `AI` Реализовать time range filtering.
* [ ] `AI` Реализовать pagination.
* [ ] `AI` Реализовать графики.
* [ ] `AI` Реализовать выбор периода.
* [ ] `AI+DEV` Определить retention policy.
* [ ] `AI` Не удалять history автоматически до согласования retention.
* [ ] `AI` Проверить производительность больших диапазонов.

---

# 36. JSON migration

JSON остаётся до окончания миграции.

Задачи:

* [ ] `AI` Проанализировать фактические JSON examples.
* [ ] `AI` Создать migration/import script.
* [ ] `AI` Импортировать камеры.
* [ ] `AI` Импортировать SNMP measurements.
* [ ] `AI` Импортировать RTSP clients.
* [ ] `AI` Импортировать WINK measurements.
* [ ] `AI` Импортировать WINK streams.
* [ ] `AI` Проверить количество импортированных записей.
* [ ] `AI` Проверить отсутствие потери данных.
* [ ] `AI` Проверить timestamps.
* [ ] `AI` Проверить duplicate handling.
* [ ] `AI` Только после успешной миграции убрать JSON storage из runtime.

---

# 37. Удаление старой архитектуры

Старые файлы:

```text
scan-snmp.py
scan-wink.py
generate-snmp-report.py
generate-wink-report.py
```

пока сохраняются.

Задачи:

* [ ] `AI` Сначала реализовать новую архитектуру.
* [ ] `AI` Реализовать новую SNMP pipeline.
* [ ] `AI` Реализовать новую WINK pipeline.
* [ ] `AI` Реализовать DB storage.
* [ ] `AI` Реализовать API.
* [ ] `AI` Реализовать worker.
* [ ] `AI` Реализовать Web UI.
* [ ] `AI` Провести regression testing.
* [ ] `AI` Выполнить migration старых данных.
* [ ] `AI` Только после этого удалить старые runtime scripts.
* [ ] `AI` При необходимости оставить migration/debug utilities.

---

# 38. Tests

Целевая структура:

```text
tests/
├── test_config.py
├── test_models.py
├── test_snmp_scanner.py
├── test_snmp_service.py
├── test_wink_scanner.py
├── test_wink_service.py
├── test_monitoring_service.py
├── test_camera_service.py
├── test_api_cameras.py
├── test_api_monitoring.py
├── test_api_history.py
└── test_health.py
```

## Unit tests

* [ ] `AI` Test settings.
* [ ] `AI` Test SNMP status.
* [ ] `AI` Test WINK status.
* [ ] `AI` Test bitrate calculation.
* [ ] `AI` Test packet loss calculation.
* [ ] `AI` Test camera validation.
* [ ] `AI` Test WINK JSON parsing.
* [ ] `AI` Test SNMP result parsing.
* [ ] `AI` Test overall camera status.
* [ ] `AI` Test error isolation.

## Database tests

* [ ] `AI` Test models.
* [ ] `AI` Test relationships.
* [ ] `AI` Test constraints.
* [ ] `AI` Test migrations.
* [ ] `AI` Test cascade behavior.
* [ ] `AI` Test timezone handling.

## API tests

* [ ] `AI` Test health.
* [ ] `AI` Test cameras CRUD.
* [ ] `AI` Test monitoring endpoints.
* [ ] `AI` Test history endpoints.
* [ ] `AI` Test validation errors.
* [ ] `AI` Test credentials are not exposed accidentally.

---

# 39. Security

Задачи:

* [ ] `AI` Проверить отсутствие passwords в source code.
* [ ] `AI` Проверить отсутствие database passwords в source code.
* [ ] `AI` Проверить `.env` handling.
* [ ] `AI` Проверить `.gitignore`.
* [ ] `AI` Не логировать credentials.
* [ ] `AI` Не возвращать passwords через обычный camera API.
* [ ] `AI` Не раскрывать RTSP credentials в HTML без явного действия пользователя.
* [ ] `AI` Проверить subprocess argument handling.
* [ ] `AI` Не использовать shell command strings без необходимости.
* [ ] `AI` Проверить path handling.
* [ ] `AI` Проверить SQL injection resistance через SQLAlchemy.
* [ ] `AI+DEV` Определить механизм хранения secrets для production.

---

# 40. PEP 8 / code quality

Задачи:

* [ ] `AI` Проверять код через Ruff.
* [ ] `AI` Использовать type hints.
* [ ] `AI` Использовать docstrings для публичных функций.
* [ ] `AI` Не допускать циклических imports.
* [ ] `AI` Соблюдать single responsibility.
* [ ] `AI` Не допускать giant modules.
* [ ] `AI` Не допускать giant functions.
* [ ] `AI` Не смешивать API/database/scanner logic.
* [ ] `AI` Не использовать глобальное mutable state без необходимости.
* [ ] `AI` Проверять imports через Ruff.
* [ ] `AI` Проверять форматирование через Ruff.
* [ ] `AI` После каждого крупного этапа выполнять lint.

---

# 41. Архитектурные правила

## Scanner

Scanner:

```text
Scanner
   |
   v
external system
```

Scanner:

* не знает о FastAPI;
* не знает о PostgreSQL;
* не выполняет ORM persistence;
* возвращает structured result;
* содержит protocol/process-specific logic.

---

## Service

Service:

```text
Service
   |
   +--> Scanner
   |
   +--> ORM / DB
```

Service отвечает за:

* business logic;
* orchestration;
* persistence;
* status calculation;
* error handling.

---

## API

API:

```text
HTTP
 |
 v
Router
 |
 v
Service
```

API не должен:

* выполнять SQL напрямую без необходимости;
* содержать monitoring business rules;
* содержать SNMP implementation;
* содержать WINK subprocess implementation.

---

## Models

Models:

* описывают структуру БД;
* relationships;
* constraints;
* database-level defaults.

Models не должны:

* запускать мониторинг;
* запускать subprocess;
* обращаться к HTTP;
* содержать orchestration.

---

## Worker

Worker:

```text
Worker
   |
   v
Monitoring service
   |
   +--> SNMP service
   |
   +--> WINK service
```

Worker не должен содержать реализацию scanners или SQL queries.

---

# 42. Systemd

Целевая deployment-модель:

```text
systemd
   |
   +-- monitoring-rsvn-web.service
   |
   +-- monitoring-rsvn-worker.service
```

Задачи:

* [ ] `AI` Создать web service.
* [ ] `AI` Создать worker service.
* [ ] `AI` Настроить restart policy.
* [ ] `AI` Настроить environment/.env.
* [ ] `AI` Настроить WorkingDirectory.
* [ ] `AI` Настроить User/Group.
* [ ] `AI` Настроить logging.
* [ ] `AI` Настроить dependency on PostgreSQL.
* [ ] `AI` Проверить graceful shutdown.
* [ ] `AI` Проверить automatic restart после failure.
* [ ] `AI` Проверить корректный startup после reboot.

---

# 43. Configuration / deployment

Создать:

```text
.env.example
```

Задачи:

* [ ] `AI` Подготовить `.env.example`.
* [ ] `AI` Документировать database settings.
* [ ] `AI` Документировать SNMP settings.
* [ ] `AI` Документировать WINK settings.
* [ ] `AI` Документировать monitoring interval.
* [ ] `AI` Документировать concurrency.
* [ ] `AI` Документировать filesystem paths.
* [ ] `AI` Убедиться, что production secrets не попадают в Git.
* [ ] `AI` Проверить запуск из независимого WorkingDirectory.

---

# 44. README

Создать:

```text
README.md
```

Задачи:

* [ ] `AI` Создать/обновить `README.md`.
* [ ] `AI` Описать назначение проекта.
* [ ] `AI` Описать архитектуру.
* [ ] `AI` Описать структуру проекта.
* [ ] `AI` Описать зависимости.
* [ ] `AI` Описать установку.
* [ ] `AI` Описать PostgreSQL setup.
* [ ] `AI` Описать Alembic.
* [ ] `AI` Описать `.env`.
* [ ] `AI` Описать запуск Web.
* [ ] `AI` Описать запуск Worker.
* [ ] `AI` Описать systemd.
* [ ] `AI` Описать тесты.
* [ ] `AI` Описать migration/import старых данных.
* [ ] `AI` Добавить troubleshooting.

---

# 45. Performance

Задачи:

* [ ] `AI` Проверить SNMP concurrency.
* [ ] `AI` Проверить WINK concurrency.
* [ ] `AI` Проверить PostgreSQL connection pool.
* [ ] `AI` Проверить Dashboard query performance.
* [ ] `AI` Проверить history query performance.
* [ ] `AI` Проверить отсутствие N+1 queries.
* [ ] `AI` Проверить большое количество камер.
* [ ] `AI` Проверить большое количество historical measurements.
* [ ] `AI` Проверить memory usage Worker.
* [ ] `AI` Проверить корректность cleanup asyncio tasks.
* [ ] `AI` Проверить длительный runtime Worker.

---

# 46. Retention

Политика хранения данных пока не утверждена.

Задачи:

* [ ] `AI+DEV` Определить срок хранения SNMP measurements.
* [ ] `AI+DEV` Определить срок хранения WINK measurements.
* [ ] `AI+DEV` Определить срок хранения stream measurements.
* [ ] `AI+DEV` Определить срок хранения RTSP clients.
* [ ] `AI` Спроектировать retention mechanism.
* [ ] `AI` Не включать автоматическое удаление до утверждения политики.

---

# 47. Migration / rollback strategy

Задачи:

* [ ] `AI+DEV` Подготовить backup PostgreSQL.
* [ ] `AI` Подготовить migration procedure.
* [ ] `AI` Подготовить rollback procedure.
* [ ] `AI+DEV` Проверить Alembic downgrade на реальной БД.
* [ ] `AI` Проверить импорт старых JSON.
* [ ] `AI` Проверить целостность данных после migration.
* [ ] `AI` Не удалять старые JSON до подтверждения успешной миграции.
* [ ] `AI` Не удалять старые Python scripts до regression testing.

---

# 48. Documentation

Уже создано:

* [x] `AI` Создать `docs/ARCHITECTURE.md`.
* [x] `AI` Создать `docs/DATABASE_SCHEMA.md`.

Осталось:

* [ ] `AI` Добавить API documentation.
* [ ] `AI` Добавить deployment documentation.
* [ ] `AI` Добавить migration documentation.
* [ ] `AI` Добавить monitoring flow documentation.
* [ ] `AI` Добавить описание структуры модулей.
* [ ] `AI` Поддерживать документацию синхронно с кодом.

---

# 49. Проверка текущего состояния репозитория

Фактическое состояние:

```text
Архитектурный аудит             DONE
Целевая архитектура             DONE
ARCHITECTURE.md                 DONE
DATABASE_SCHEMA.md              DONE

pyproject.toml                  DONE
Application configuration       DONE
Database infrastructure         DONE

ORM models                      DONE
Alembic infrastructure          DONE
Initial migration               DONE

Alembic real DB validation      TODO

Application package             NEXT
Logging                         TODO

SNMP scanner                    TODO
SNMP service                    TODO
SNMP status                     TODO

WINK scanner                    TODO
WINK service                    TODO
WINK status                     TODO

Monitoring service              TODO
Overall camera status            TODO

Camera service / CRUD           TODO
Credentials integration         TODO

FastAPI application              TODO
Pydantic schemas                TODO
API cameras                     TODO
API monitoring                  TODO
API history                     TODO
API health                      TODO

Monitoring worker               TODO

Excel import/export             TODO
JSON migration                  TODO

Web UI                           TODO
Dashboard                        TODO
History UI                       TODO

Tests                            TODO
Security audit                   TODO
PEP 8 / Ruff                     TODO

systemd                          TODO
Deployment                       TODO
README                           TODO

Performance testing              TODO
Retention policy                 TODO
Migration / rollback             TODO

Final regression testing         TODO
Production deployment            TODO
Final QA                         TODO
```

---

# 50. Что НЕ считать выполненным

Следующие пункты нельзя считать выполненными только потому, что соответствующие файлы уже существуют:

* наличие `pyproject.toml` не означает готовое приложение;
* наличие `app/database.py` не означает рабочую БД;
* наличие ORM models не означает проверенную работу с PostgreSQL;
* наличие `alembic.ini` не означает успешно применённые migrations;
* наличие `0001_initial_schema.py` не означает, что migration реально проверена;
* наличие FastAPI в dependencies не означает работающий API;
* наличие entry points не означает, что Web/Worker запускаются;
* наличие configuration settings не означает, что они используются всеми компонентами;
* наличие архитектурной документации не означает реализацию архитектуры;
* наличие моделей не означает наличие services;
* наличие services не означает наличие API;
* наличие API не означает наличие Web UI;
* наличие Worker entry point не означает работающий monitoring loop;
* наличие старых scanner scripts не означает новую SNMP/WINK pipeline.

---

# 51. Текущая точка проекта

## Фактически завершено

```text
Архитектура
     DONE
       |
       v
Database design
     DONE
       |
       v
Configuration
     DONE
       |
       v
Database infrastructure
     DONE
       |
       v
ORM models
     DONE
       |
       v
Alembic infrastructure
     DONE
       |
       v
Initial migration
     DONE
       |
       v
Application package
     NEXT
       |
       v
Logging
       |
       v
SNMP / WINK scanners
       |
       v
Services
       |
       v
FastAPI / Worker
       |
       v
Tests
       |
       v
Web UI
       |
       v
Data migration
       |
       v
Production
```

---

# 52. Ближайший этап разработки

## NEXT STEP

> **Создать Application package и минимальные entry points Web/Worker.**

Порядок дальнейшей работы:

```text
1. app/__init__.py
       |
       v
2. app/main.py
       |
       v
3. app/worker.py
       |
       v
4. проверить entry points
       |
       v
5. logging_config.py
       |
       v
6. scanners/
       |
       +---- snmp_scanner.py
       |
       +---- wink_scanner.py
       |
       v
7. services/
       |
       +---- camera_service.py
       +---- snmp_service.py
       +---- wink_service.py
       +---- monitoring_service.py
       |
       v
8. Pydantic schemas
       |
       v
9. FastAPI routers
       |
       v
10. Worker monitoring loop
       |
       v
11. Tests
       |
       v
12. Excel / JSON migration
       |
       v
13. Web UI
       |
       v
14. systemd / deployment
```

---

# 53. Правила дальнейшей разработки

1. Не переписывать рабочую логику без необходимости.
2. Сохранять существующую семантику SNMP и WINK.
3. Не удалять credentials камер.
4. Не выводить credentials в обычных логах/API.
5. PostgreSQL является source of truth после завершения миграции.
6. JSON использовать для migration/debug/export, а не как runtime database.
7. Scanner не должен обращаться к PostgreSQL напрямую.
8. API не должен содержать бизнес-логику.
9. Business logic должна находиться в services.
10. ORM models не должны содержать orchestration.
11. Worker не должен содержать SQL/HTTP implementation details.
12. Все изменения схемы БД выполнять через Alembic.
13. Не использовать `Base.metadata.create_all()` как production migration mechanism.
14. Не считать наличие файла доказательством реализации функции.
15. После каждого крупного этапа запускать автоматические проверки.
16. Перед удалением старого кода выполнять regression check.
17. Не удалять старые данные до подтверждения успешной миграции.
18. Не допускать silent exception handling.
19. Не допускать hardcoded production secrets.
20. Поддерживать `TODO.md`, `ARCHITECTURE.md` и `DATABASE_SCHEMA.md` синхронными с кодом.
21. Не создавать новые параллельные реализации одной и той же business logic для Web и Worker.
22. Manual monitoring и scheduled monitoring должны использовать одни и те же services.
23. SNMP и WINK должны оставаться независимыми pipeline.
24. Ошибка одной камеры не должна останавливать весь Worker.
25. Не удалять старые scripts до завершения regression testing.

---

# 54. Критерий готовности проекта

Проект считается готовым к production только после выполнения всех обязательных этапов:

```text
[ ] PostgreSQL работает
[x] ORM models созданы
[x] Alembic infrastructure создана
[x] Initial migration создана
[ ] Alembic migrations проверены на реальной PostgreSQL

[ ] Application package готов
[ ] Logging готов

[ ] SNMP scanner работает
[ ] WINK scanner работает
[ ] SNMP service работает
[ ] WINK service работает
[ ] Monitoring service работает
[ ] Overall camera status работает

[ ] FastAPI работает
[ ] Camera CRUD работает
[ ] Monitoring API работает
[ ] History API работает
[ ] Health API работает

[ ] Worker работает

[ ] Excel import/export работает
[ ] Старые JSON данные мигрированы

[ ] Web UI работает
[ ] Dashboard работает
[ ] History UI работает

[ ] Unit tests проходят
[ ] Database tests проходят
[ ] API tests проходят
[ ] Ruff проходит

[ ] Security audit пройден
[ ] Performance проверена

[ ] systemd настроен
[ ] README актуален
[ ] Deployment documentation готова

[ ] Regression testing пройден
[ ] Migration/rollback проверены
[ ] Старые runtime scripts удалены
    или окончательно переведены в migration/debug utilities

[ ] Final QA
[ ] Production deployment
```

---

# 55. Текущая точка остановки

**ORM и Alembic уже реализованы.**

Текущая рабочая точка:

```text
app/models/                  DONE
migrations/                  DONE
0001_initial_schema.py       DONE

        ↓

app/__init__.py              NEXT
app/main.py                  NEXT
app/worker.py                NEXT
```

**Следующий этап разработки: Application package — создание `app/__init__.py`, `app/main.py` и `app/worker.py`, затем их базовая проверка и переход к logging/scanners.**
