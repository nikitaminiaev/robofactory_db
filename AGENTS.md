# AGENTS.md - RoboFactory Database Project

## Build Commands

- Too containers:
  - api - python, fastapi, uviorn
  - db - postgres
- Build containers: `docker compose build`
- Start services: `docker compose up -d`
- Run API: `uvicorn main:app --host 0.0.0.0 --reload`
- Run API in container: `docker exec api python main.py`

## Code Quality Commands

- Run type checking on a file: `docker exec api pyright /usr/src/api/<relative_path_to_file>`

run tests manually in api container (tests are at /usr/src/tests/):

    # run all tests
    docker exec api python -m pytest /usr/src/tests/ -v

    # run specific file
    docker exec api python -m pytest /usr/src/tests/unit/test_git_manager.py -v

    # run with code coverage
    docker exec api pip install pytest-cov
    docker exec api python -m pytest /usr/src/tests/ --cov=api --cov-report=html

## Database Commands
before `cd database`
- Create migration: `alembic revision --autogenerate -m "message"`
- Run migrations: `alembic upgrade head`
- Rollback: `alembic downgrade -1`
- Restore DB dump: `psql -U admin -h db -p 5433 < db/dump/schema.sql`

## Code Style Guidelines

### Imports

- Use relative imports within the project
- Standard library first, then third-party, then local imports
- Group imports with blank lines between groups

### Type Hints

- Use typing module extensively for all function parameters and return types
- Use Union types for optional parameters: `Optional[str] = None`

### Error Handling

- Use try/except blocks with specific exception types
- Use early returns to avoid nested if statements
- Log errors with descriptive messages

### Database Patterns

- Use context managers for database sessions
- Use repository pattern for data access
- Use selectinload for eager loading relationships
- Use dependency injection with FastAPI Depends()

### API Design

- Use Pydantic models for request/response validation
- Return appropriate HTTP status codes with FastAPI HTTPException
- Use meaningful Russian error messages for API responses

## Entity Relationships Summary

### Core Entities and Key Relationships

- **Module** (central entity for robotic modules)
  - One-to-One: `bounding_contour` (to BoundingContour)
  - Many-to-One: `service` (to Service)
  - Many-to-One: `interface_object_id` (to InterfaceObject)
  - Many-to-Many (self-referential hierarchy): `children` and `parents` (via `parent_child_module` association)
  - Many-to-Many: `streams` (via `module_stream`)
  - Many-to-Many: `platforms` (via `module_platform`)
  - Many-to-Many: `boundaries` (via `module_boundary`)
- **Service** (groups modules)
  - Many-to-One: `platform_id` (to Platform)
  - One-to-Many: `modules` (to Module)
- **Platform** (deployment environments)
  - One-to-Many: `services` (to Service)
- **Stream** (data flows)
  - Many-to-Many: `modules` (via `module_stream`)
- **ModuleBoundary** (defines module interfaces/boundaries)
  - Many-to-One: `interface_in` and `interface_out` (to InterfaceObject)
  - Many-to-One: `stream` (to Stream)
  - Many-to-Many: `modules` (via `module_boundary`)
- **BoundingContour** (geometric boundaries for modules)
  - One-to-One: `module` (to Module)
  - Self-Referential: `parent` (hierarchy)
- **InterfaceObject** (interface definitions; referenced from ModuleBoundary)
- **ModuleRole** (roles in parent-child relationships)
- **ModuleUpdateReason** (tracks module updates)
  - Many-to-One: `old_module` and `new_module` (to Module)
- **ModuleVersion** (version history with Git integration)
  - Many-to-One: `module_id` (to Module)
  - Stores: version_number, commit_hash, description, git_repo_path, is_released, created_ts

### Association Tables (Many-to-Many)

- `parent_child_module`: Links Modules in hierarchy with coordinates and role.
- `module_stream`: Links Modules to Streams.
- `module_platform`: Links Modules to Platforms.
- `module_boundary`: Links Modules to ModuleBoundaries.

### Overall Structure

Modules form a parent-child hierarchy. Services belong to Platforms and contain Modules. Boundaries reference InterfaceObjects and Streams. Updates are tracked via ModuleUpdateReason.

## Модульное копирование и версионирование

Система поддерживает копирование модулей с автоматическим версионированием и интеграцией с Git для отслеживания изменений в BREP файлах.

### API эндпоинты

- `POST /api/modules/{module_id}/copy`: Копирует модуль с указанием нового автора, номера версии и описания. Копирует связи parent-child, bounding_contour, инициализирует Git репозиторий и создаёт коммит.
- `POST /api/modules/{module_id}/brep`: Сохраняет BREP файл в директорию `api/resources/brep_files/{module_id}/`, обновляет bounding_contour, выполняет Git коммит и создаёт новую версию.
- `GET /api/modules/{module_id}/versions`: Возвращает список версий модуля.
- `GET /api/modules/{module_id}/commits`: Возвращает историю Git коммитов.

### Версионирование

Каждая версия хранит номер, хэш коммита, описание, путь к репозиторию и статус релиза. Версии создаются при копировании и сохранении файлов.

### Git интеграция

Каждый модуль имеет собственный Git репозиторий для отслеживания BREP файлов. Коммиты создаются автоматически при изменениях.

## FreeCAD PLMplugin (смежный проект)

Плагин расположен в `/media/ssd_1_9tb/PycharmProjects/freecadPlugin/PLMplugin/`. Интеграционный мост между FreeCAD и robofactory_db.

### Функционал
- **Загрузка моделей** из БД в FreeCAD: рекурсивная загрузка объектов с детьми, BREP-геометрией, координатами; создание `App::Part` с вложенными `Part::Feature`
- **Выгрузка моделей** из FreeCAD в БД: извлечение BREP, координат, отправка POST/PATCH на API
- **Навигация по иерархии** сборок: переход вверх/вниз по дереву parent-child
- **WebSocket-сервер** (порт 8765): удалённое управление FreeCAD из AI-агентов — выполнение Python-кода (`freecad_executor.py`) или вызов PLM-функций (`plm_functions.py`)
- **MCP-сервер** (порт 9877): интеграция с AI-ассистентами через Model Context Protocol — скриншоты, сравнение геометрии, выполнение скриптов

### Архитектура
- `InitGui.py` — регистрирует верстак "PLM" в FreeCAD
- `main_window.py` — главное окно GUI (PySide2), дерево объектов, кнопки загрузки/выгрузки
- `api_client.py` — HTTP-клиент к robofactory_db (localhost:8000)
- `socket_client.py` + `client_panel.py` — WebSocket клиент для удалённого управления
- `plm_functions.py` + `function_registry.py` — реестр функций, вызываемых по имени из WebSocket
- `freecad_executor.py` — безопасное выполнение Python-кода в контексте FreeCAD
- `cad_utils.py` — утилиты: создание деталей из BREP, извлечение BREP, скриншоты, сравнение геометрии
- `mcp/` — MCP-сервер (FastMCP) для AI-интеграции
- `widgets.py` — кастомный QTreeWidget с ленивой загрузкой детей

### API эндпоинты robofactory_db, используемые плагином
| Метод | Эндпоинт | Назначение |
|-------|----------|------------|
| GET | `/api/basic_objects/count` | Количество объектов |
| GET | `/api/basic_object?name=` | Поиск по имени |
| GET | `/api/basic_objects/top_level` | Корневые объекты |
| GET | `/api/basic_object/{id}` | Объект по ID (с детьми) |
| GET | `/api/basic_object/{id}/parent_ids` | ID родителей |
| GET | `/api/basic_objects/{id}/children` | Дети объекта |
| POST | `/api/basic_object/` | Создание объекта |
| PATCH | `/api/basic_object/{id}` | Обновление (BREP, имя, координаты) |
| PATCH | `/api/parent_child_module/{record_id}` | Обновление координат parent-child |
