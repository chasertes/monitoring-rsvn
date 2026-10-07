# Monitoring RSVN — TODO.md

> Дорожная карта разработки и архитектурной переработки проекта `monitoring-rsvn`.
>
> Документ является рабочей точкой продолжения разработки.
> После каждого значимого этапа статус задач должен обновляться здесь.

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

Перевести текущий скриптовый мониторинг SNMP/WINK на полноценное модульное приложение:

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
* не зависеть от JSON-файлов как от основного хранилища.

---

# 1. Текущее состояние проекта

## 1.1 Исходный проект

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

---

# 2. Что уже сделано

## 2.1 Архитектурное проектирование

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

## 2.2 Проектирование PostgreSQL schema

* [x] `AI` Определена предварительная схема PostgreSQL.
* [x] `AI` Определена таблица `cameras`.
* [x] `AI` Определена таблица `camera_credentials`.
* [x] `AI` Определена таблица `snmp_measurements`.
* [x] `AI` Определена таблица `rtsp_clients`.
* [x] `AI` Определена таблица `wink_measurements`.
* [x] `AI` Определена таблица `wink_streams`.
* [x] `AI` Определены основные foreign keys.
* [x] `AI` Определены основные индексы.
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

## 2.3 Python dependencies

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
* [x] `AI` Добавлен httpx для API-тестов.
* [x] `AI` Добавлен Ruff.
* [x] `AI` Настроен pytest.
* [x] `AI` Настроен Ruff.
* [x] `AI` Настроены entry points:

```text
monitoring-rsvn-web
monitoring-rsvn-worker
```

---

## 2.4 Application configuration

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

# 3. Database infrastructure

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

пока является только инфраструктурой БД.

ORM-модели и миграции ещё не созданы.

---

# 4. Критически важный следующий этап — ORM models

## 4.1 Создание структуры моделей

Создать:

```text
app/models/
├── __init__.py
├── camera.py
├── credentials.py
├── snmp.py
├── rtsp_client.py
└── wink.py
```

Задачи:

* [ ] `AI` Создать `app/models/__init__.py`.
* [ ] `AI` Создать `Camera`.
* [ ] `AI` Создать `CameraCredential`.
* [ ] `AI` Создать `SnmpMeasurement`.
* [ ] `AI` Создать `RtspClient`.
* [ ] `AI` Создать `WinkMeasurement`.
* [ ] `AI` Создать `WinkStream`.
* [ ] `AI` Подключить все модели к `Base`.
* [ ] `AI` Проверить все foreign keys.
* [ ] `AI` Проверить cascade behavior.
* [ ] `AI` Проверить indexes.
* [ ] `AI` Проверить unique constraints.
* [ ] `AI` Проверить nullable/non-nullable поля.
* [ ] `AI` Проверить timezone-aware datetime.
* [ ] `AI` Не использовать `Base.metadata.create_all()` как механизм production migrations.

---

# 5. Alembic

## 5.1 Создание миграционной инфраструктуры

* [ ] `AI` Создать `alembic.ini` или эквивалентную конфигурацию.
* [ ] `AI` Создать `migrations/`.
* [ ] `AI` Создать `migrations/env.py`.
* [ ] `AI` Настроить async SQLAlchemy/Alembic.
* [ ] `AI` Подключить metadata всех моделей.
* [ ] `AI` Не хранить database password в migration files.
* [ ] `AI` Получать database URL через application settings.

## 5.2 Initial migration

* [ ] `AI` Создать initial migration.
* [ ] `AI` Создать `cameras`.
* [ ] `AI` Создать `camera_credentials`.
* [ ] `AI` Создать `snmp_measurements`.
* [ ] `AI` Создать `rtsp_clients`.
* [ ] `AI` Создать `wink_measurements`.
* [ ] `AI` Создать `wink_streams`.
* [ ] `AI` Создать все foreign keys.
* [ ] `AI` Создать все обязательные indexes.
* [ ] `AI` Проверить upgrade.
* [ ] `AI` Проверить downgrade.
* [ ] `AI` Проверить повторный запуск migration chain.

---

# 6. Application package

Сейчас `pyproject.toml` уже ожидает:

```text
app.main:main
app.worker:main
```

Но этих модулей пока нет.

Задачи:

* [ ] `AI` Создать `app/__init__.py`.
* [ ] `AI` Создать `app/main.py`.
* [ ] `AI` Создать `app/worker.py`.
* [ ] `AI` Проверить запуск:

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

# 7. Logging

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

---

# 8. SNMP migration

## 8.1 Целевая архитектура

Старое:

```text
ThreadPoolExecutor
        |
        +--> asyncio.run()
        |
        +--> asyncio.run()
        |
        +--> asyncio.run()
```

Новое:

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
* [ ] `AI` Создать `app/scanners/snmp_scanner.py`.
* [ ] `AI` Перенести SNMP protocol logic.
* [ ] `AI` Удалить `ThreadPoolExecutor` из новой реализации.
* [ ] `AI` Не использовать `asyncio.run()` для каждой камеры.
* [ ] `AI` Использовать единый event loop.
* [ ] `AI` Использовать `asyncio.Semaphore`.
* [ ] `AI` Перенести SNMP timeout.
* [ ] `AI` Перенести retries.
* [ ] `AI` Проверить PySNMP 7.x API.
* [ ] `AI` Проверить SNMP GET.
* [ ] `AI` Проверить SNMP WALK.
* [ ] `AI` Проверить TCP table walk.
* [ ] `AI` Обработать timeout.
* [ ] `AI` Обработать SNMP error status.
* [ ] `AI` Обработать недоступную камеру.
* [ ] `AI` Убрать беззвучный `except Exception: pass`.
* [ ] `AI` Вернуть scanner structured result.
* [ ] `AI` Не позволять scanner напрямую записывать данные в БД.

---

# 9. SNMP service

Создать:

```text
app/services/snmp_service.py
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

# 10. SNMP status

Существующие бизнес-правила должны быть сохранены.

Проверки:

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
* [ ] `AI` Не изменять исходные измеренные значения при расчёте статуса.

---

# 11. WINK / RTSP migration

## 11.1 Scanner

Создать:

```text
app/scanners/wink_scanner.py
```

Задачи:

* [ ] `AI` Перенести запуск `wink-rtsp-stats.exe`.
* [ ] `AI` Перенести subprocess logic.
* [ ] `AI` Использовать настроенный executable path.
* [ ] `AI` Использовать ограничение `wink_concurrency`.
* [ ] `AI` Реализовать timeout.
* [ ] `AI` Обработать отсутствующий executable.
* [ ] `AI` Обработать ненулевой exit code.
* [ ] `AI` Обработать invalid JSON.
* [ ] `AI` Обработать пустой результат.
* [ ] `AI` Вернуть structured Python result.
* [ ] `AI` Не записывать данные непосредственно в БД.

---

# 12. WINK service

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

# 13. WINK status

Сохранить текущие правила:

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
* [ ] `AI` Проверить случай нескольких streams.
* [ ] `AI` Проверить отсутствие streams.

---

# 14. Monitoring service

Создать:

```text
app/services/monitoring_service.py
```

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

---

# 15. Общий статус камеры

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

---

# 16. Camera models и CRUD

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

# 17. Credentials

Критическое правило:

> Пароли камер и RTSP credentials не удаляются из рабочего процесса.

Задачи:

* [ ] `AI` Реализовать `CameraCredential`.
* [ ] `AI` Сохранять username.
* [ ] `AI` Сохранять password.
* [ ] `AI` Сохранять SNMP community.
* [ ] `AI` Использовать credentials для WINK.
* [ ] `AI` Использовать SNMP community для SNMP.
* [ ] `AI` Не выводить password в обычных API responses.
* [ ] `AI` Не писать password в logs.
* [ ] `AI+DEV` Отдельно решить вопрос шифрования credentials.
* [ ] `AI` Не делать encryption блокером текущего этапа.

---

# 18. FastAPI application

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

# 19. Pydantic schemas

Создать:

```text
app/schemas/
├── __init__.py
├── camera.py
├── monitoring.py
└── reports.py
```

Задачи:

* [ ] `AI` Создать request schemas.
* [ ] `AI` Создать response schemas.
* [ ] `AI` Создать camera schemas.
* [ ] `AI` Создать monitoring schemas.
* [ ] `AI` Создать history schemas.
* [ ] `AI` Скрыть credentials из обычных responses.
* [ ] `AI` Валидировать входные данные через Pydantic.

---

# 20. API cameras

Создать:

```text
app/api/cameras.py
```

Endpoints:

```text
GET    /api/cameras
POST   /api/cameras
GET    /api/cameras/{id}
PUT    /api/cameras/{id}
DELETE /api/cameras/{id}

POST   /api/cameras/{id}/test-snmp
POST   /api/cameras/{id}/test-rtsp
```

Задачи:

* [ ] `AI` Реализовать GET cameras.
* [ ] `AI` Реализовать POST camera.
* [ ] `AI` Реализовать GET camera.
* [ ] `AI` Реализовать PUT camera.
* [ ] `AI` Реализовать DELETE camera.
* [ ] `AI` Реализовать enable/disable.
* [ ] `AI` Реализовать manual SNMP test.
* [ ] `AI` Реализовать manual RTSP test.

---

# 21. API monitoring

Создать:

```text
app/api/monitoring.py
```

Endpoints:

```text
GET /api/monitoring/summary
GET /api/cameras/{id}/status
GET /api/cameras/{id}/snmp
GET /api/cameras/{id}/wink
GET /api/problems
```

Задачи:

* [ ] `AI` Реализовать monitoring summary.
* [ ] `AI` Реализовать current camera status.
* [ ] `AI` Реализовать current SNMP state.
* [ ] `AI` Реализовать current WINK state.
* [ ] `AI` Реализовать problems endpoint.

---

# 22. API history

Создать:

```text
app/api/history.py
```

Endpoints:

```text
GET /api/cameras/{id}/history/snmp
GET /api/cameras/{id}/history/wink
```

Задачи:

* [ ] `AI` Реализовать history SNMP.
* [ ] `AI` Реализовать history WINK.
* [ ] `AI` Добавить period filters.
* [ ] `AI` Добавить pagination.
* [ ] `AI` Добавить сортировку по timestamp.
* [ ] `AI` Не загружать неограниченное количество measurements одним запросом.

---

# 23. API health

Создать:

```text
app/api/health.py
```

Задачи:

* [ ] `AI` Реализовать `/health`.
* [ ] `AI` Реализовать `/health/ready`.
* [ ] `AI` Проверять PostgreSQL для readiness.
* [ ] `AI` Не считать HTTP 200 доказательством работоспособности мониторинга.
* [ ] `AI` При необходимости добавить worker status.

---

# 24. Monitoring worker

Создать:

```text
app/worker.py
```

Worker должен:

```text
start
  |
  v
load enabled cameras
  |
  v
monitoring cycle
  |
  +--> SNMP
  |
  +--> WINK
  |
  v
save results
  |
  v
sleep
  |
  +----> next cycle
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

---

# 25. Excel import/export

`cameras.xlsx` больше не должен быть runtime source of truth.

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

Endpoints:

```text
POST /api/cameras/import
GET  /api/cameras/export
```

---

# 26. Web UI

Целевая структура:

```text
app/web/
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
* [ ] `AI` Добавить возможность просмотра credentials без раскрытия в обычном списке.
* [ ] `AI` Добавить ручной SNMP test.
* [ ] `AI` Добавить ручной RTSP test.
* [ ] `AI` Добавить графики истории.

---

# 27. Dashboard

Dashboard должен отображать:

```text
Total cameras
Online
Warning
Error
Offline
Disabled
```

Для каждой камеры:

```text
camera
operator
IP
SNMP status
WINK status
overall status
last measurement
```

Задачи:

* [ ] `AI` Реализовать summary endpoint.
* [ ] `AI` Реализовать dashboard.
* [ ] `AI` Реализовать получение последнего measurement эффективно.
* [ ] `AI` Не выполнять N+1 SQL queries.
* [ ] `AI` Проверить производительность Dashboard.

---

# 28. History

История должна позволять анализировать:

```text
SNMP
WINK
bitrate
packet loss
jitter
RTSP clients
interface speed
uptime
status changes
```

Задачи:

* [ ] `AI` Реализовать historical queries.
* [ ] `AI` Реализовать time range filtering.
* [ ] `AI` Реализовать pagination.
* [ ] `AI` Реализовать графики.
* [ ] `AI` Реализовать выбор периода.
* [ ] `AI+DEV` Определить retention policy.
* [ ] `AI` Не удалять history автоматически до согласования retention.

---

# 29. JSON migration

Старые директории:

```text
scanned_metrics/
metrics_json/
```

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
* [ ] `AI` Только после успешной миграции убрать JSON storage из runtime.

---

# 30. Удаление старой архитектуры

Старые файлы:

```text
scan-snmp.py
scan-wink.py
generate-snmp-report.py
generate-wink-report.py
```

пока НЕ удалять.

Задачи:

* [ ] `AI` Сначала реализовать новую архитектуру.
* [ ] `AI` Реализовать новую SNMP pipeline.
* [ ] `AI` Реализовать новую WINK pipeline.
* [ ] `AI` Реализовать DB storage.
* [ ] `AI` Реализовать API.
* [ ] `AI` Реализовать worker.
* [ ] `AI` Провести regression testing.
* [ ] `AI` Только после этого удалить старые runtime scripts.
* [ ] `AI` При необходимости оставить migration/debug utilities.

---

# 31. Tests

Создать:

```text
tests/
```

Структура:

```text
tests/
├── unit/
├── integration/
└── api/
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

## Database tests

* [ ] `AI` Test models.
* [ ] `AI` Test relationships.
* [ ] `AI` Test constraints.
* [ ] `AI` Test migrations.
* [ ] `AI` Test cascade behavior.

## API tests

* [ ] `AI` Test health.
* [ ] `AI` Test cameras CRUD.
* [ ] `AI` Test monitoring endpoints.
* [ ] `AI` Test history endpoints.
* [ ] `AI` Test validation errors.
* [ ] `AI` Test credentials are not exposed accidentally.

---

# 32. Security

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

# 33. PEP 8 / code quality

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

Проверка:

```bash
ruff check .
ruff format --check .
```

---

# 34. Архитектурные правила

## Scanner

Scanner отвечает только за взаимодействие с внешней системой:

```text
SNMP
WINK executable
```

Scanner НЕ должен:

```text
write database
handle HTTP
render HTML
```

## Service

Service отвечает за:

```text
business logic
orchestration
database interaction
status calculation
```

## API

API отвечает только за:

```text
HTTP
validation
serialization
dependency injection
```

## Models

Models отвечают только за:

```text
database schema
relationships
constraints
```

## Worker

Worker отвечает только за:

```text
scheduled monitoring
```

---

# 35. Systemd

После реализации приложения подготовить:

```text
systemd/
├── monitoring-rsvn-web.service
└── monitoring-rsvn-worker.service
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

---

# 36. Configuration / deployment

Создать:

```text
config/
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

---

# 37. README

Текущий репозиторий должен иметь полноценный README.

Задачи:

* [ ] `AI` Создать/обновить `README.md`.
* [ ] `AI` Описать назначение проекта.
* [ ] `AI` Описать архитектуру.
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

---

# 38. Performance

Задачи:

* [ ] `AI` Проверить SNMP concurrency.
* [ ] `AI` Проверить WINK concurrency.
* [ ] `AI` Проверить PostgreSQL connection pool.
* [ ] `AI` Проверить Dashboard query performance.
* [ ] `AI` Проверить history query performance.
* [ ] `AI` Проверить отсутствие N+1 queries.
* [ ] `AI` Проверить большое количество камер.
* [ ] `AI` Проверить большое количество historical measurements.
* [ ] `AI` Проверить memory usage worker.
* [ ] `AI` Проверить корректность cleanup asyncio tasks.

---

# 39. Retention

История является одной из основных функций новой системы.

Задачи:

* [ ] `AI+DEV` Определить срок хранения SNMP measurements.
* [ ] `AI+DEV` Определить срок хранения WINK measurements.
* [ ] `AI+DEV` Определить срок хранения stream measurements.
* [ ] `AI+DEV` Определить срок хранения RTSP clients.
* [ ] `AI` Спроектировать retention mechanism.
* [ ] `AI` Не включать автоматическое удаление до утверждения политики.

---

# 40. Migration / rollback strategy

Задачи:

* [ ] `AI` Подготовить backup PostgreSQL.
* [ ] `AI` Подготовить migration procedure.
* [ ] `AI` Подготовить rollback procedure.
* [ ] `AI` Проверить Alembic downgrade.
* [ ] `AI` Проверить импорт старых JSON.
* [ ] `AI` Проверить целостность данных после migration.
* [ ] `AI` Не удалять старые JSON до подтверждения успешной миграции.
* [ ] `AI` Не удалять старые Python scripts до regression testing.

---

# 41. Documentation

Уже существуют:

```text
docs/ARCHITECTURE.md
docs/DATABASE_SCHEMA.md
```

Задачи:

* [x] `AI` Создать architecture documentation.
* [x] `AI` Создать database schema documentation.
* [ ] `AI` Добавить API documentation.
* [ ] `AI` Добавить deployment documentation.
* [ ] `AI` Добавить migration documentation.
* [ ] `AI` Добавить monitoring flow documentation.
* [ ] `AI` Поддерживать документацию синхронно с кодом.

---

# 42. Проверка текущего состояния репозитория

На момент обновления TODO фактически существуют:

```text
TODO.md
pyproject.toml

app/
    config.py
    database.py

docs/
    ARCHITECTURE.md
    DATABASE_SCHEMA.md

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

app/models/
app/schemas/
app/services/
app/scanners/
app/api/
app/web/

migrations/
tests/
systemd/
config/
```

Следовательно, проект находится между этапами:

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
     NEXT
       |
       v
Alembic
       |
       v
Scanners / Services
       |
       v
FastAPI / Worker
       |
       v
Web UI
       |
       v
Tests
       |
       v
Migration
       |
       v
Production
```

---

# 43. Что НЕ считать выполненным

Следующие пункты нельзя считать выполненными только потому, что соответствующие документы или зависимости уже существуют:

* наличие `pyproject.toml` не означает готовое приложение;
* наличие `app/database.py` не означает готовую БД;
* наличие `docs/DATABASE_SCHEMA.md` не означает созданные таблицы;
* наличие `docs/ARCHITECTURE.md` не означает реализованную архитектуру;
* наличие FastAPI в dependencies не означает работающий API;
* наличие SQLAlchemy не означает наличие ORM models;
* наличие Alembic в dependencies не означает наличие migrations;
* наличие entry points в `pyproject.toml` не означает, что web/worker уже запускаются;
* наличие `asyncpg` не означает подключение к рабочему PostgreSQL;
* наличие конфигурационных параметров не означает их использование всеми компонентами.

---

# 44. Текущая точка проекта

## Фактический статус

```text
Исходный аудит                 DONE
Целевая архитектура             DONE
ARCHITECTURE.md                 DONE
DATABASE_SCHEMA.md              DONE

pyproject.toml                  DONE
Application configuration       DONE
Database infrastructure         DONE

ORM models                      TODO
Alembic infrastructure          TODO
Initial DB migration             TODO

SNMP scanner                    TODO
SNMP service                    TODO
WINK scanner                    TODO
WINK service                    TODO
Monitoring service              TODO

FastAPI application              TODO
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
Logging                          TODO
Security audit                   TODO
Performance testing              TODO
systemd                          TODO
README                           TODO
Production deployment            TODO
Final QA                         TODO
```

---

# 45. Ближайший этап разработки

## NEXT STEP

> **Создать SQLAlchemy ORM-модели на основании утверждённой схемы `docs/DATABASE_SCHEMA.md`.**

Порядок:

```text
1. app/__init__.py
       ↓
2. app/models/__init__.py
       ↓
3. camera.py
       ↓
4. credentials.py
       ↓
5. snmp.py
       ↓
6. rtsp_client.py
       ↓
7. wink.py
       ↓
8. подключение моделей к Base
       ↓
9. проверка relationships
       ↓
10. Alembic
       ↓
11. initial migration
```

До завершения этого этапа:

* не удалять старые скрипты;
* не удалять JSON storage;
* не начинать Web UI;
* не считать PostgreSQL migration завершённой;
* не переносить старую бизнес-логику вслепую.

---

# 46. Правила дальнейшей разработки

1. Не переписывать рабочую логику без необходимости.
2. Сохранять существующую семантику SNMP и WINK.
3. Не удалять credentials камер.
4. Не выводить credentials в обычных логах/API.
5. PostgreSQL является source of truth после завершения миграции.
6. JSON использовать только для migration/debug/export после перехода.
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

---

# 47. Критерий готовности проекта

Проект считается готовым к production только после выполнения всех обязательных этапов:

```text
[ ] PostgreSQL работает
[ ] Alembic migrations работают
[ ] ORM models готовы
[ ] SNMP scanner работает
[ ] WINK scanner работает
[ ] Services готовы
[ ] Worker работает
[ ] FastAPI работает
[ ] Camera CRUD работает
[ ] Monitoring API работает
[ ] History API работает
[ ] Web UI работает
[ ] Excel import/export работает
[ ] Старые JSON данные мигрированы
[ ] Tests проходят
[ ] Ruff проходит
[ ] Security audit пройден
[ ] Performance проверена
[ ] systemd настроен
[ ] README актуален
[ ] Regression testing пройден
[ ] Старые runtime scripts удалены или окончательно переведены в migration/debug utilities
```

---

# 48. Текущая точка остановки

**Мы остановились непосредственно перед созданием ORM-моделей.**

Текущая последовательность разработки:

```text
                    DONE
                     |
                     v
            Architecture design
                     |
                     v
             Database schema
                     |
                     v
              pyproject.toml
                     |
                     v
             app/config.py
                     |
                     v
            app/database.py
                     |
                     v
              >>> NEXT <<<
                     |
                     v
             SQLAlchemy Models
                     |
                     v
              Alembic migration
                     |
                     v
             SNMP / WINK layers
                     |
                     v
             FastAPI + Worker
                     |
                     v
                  Web UI
                     |
                     v
                Migration
                     |
                     v
               Tests / QA
                     |
                     v
                Production
```

**Следующее конкретное действие:**

> Создать `app/models/` и реализовать шесть ORM-моделей (`Camera`, `CameraCredential`, `SnmpMeasurement`, `RtspClient`, `WinkMeasurement`, `WinkStream`) строго по `docs/DATABASE_SCHEMA.md`, после чего подготовить первую Alembic migration.
