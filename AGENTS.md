# AGENTS.md - RoboFactory Database Project

## Build Commands
- Too containers:
    - api - python, fastapi, uviorn
    - db - postgres
- Build containers: `docker-compose build`
- Start services: `docker-compose up -d`
- Run API: `uvicorn main:app --host 0.0.0.0 --reload`
- Run API in container: `docker exec api python main.py`

## Code Quality Commands
- Run type checking on a file: `docker exec api pyright /usr/src/api/<relative_path_to_file>`

## Database Commands
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

### Association Tables (Many-to-Many)
- `parent_child_module`: Links Modules in hierarchy with coordinates and role.
- `module_stream`: Links Modules to Streams.
- `module_platform`: Links Modules to Platforms.
- `module_boundary`: Links Modules to ModuleBoundaries.

### Overall Structure
Modules form a parent-child hierarchy. Services belong to Platforms and contain Modules. Boundaries reference InterfaceObjects and Streams. Updates are tracked via ModuleUpdateReason.</content>
<parameter name="filePath">/media/ssd_1_9tb/PycharmProjects/robofactory_db/AGENTS.md