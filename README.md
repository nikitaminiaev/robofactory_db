## Быстрый старт

```bash
./install.sh   # первый запуск: создаёт .env, собирает и запускает контейнеры
./start.sh     # последующие запуски
```

После запуска:
- API: http://localhost:8000
- DB:  localhost:5433

Остановить:

    docker compose down

---

## Разработка

### Войти в контейнер API

    docker exec -ti api bash

### Создать миграцию

```bash
cd database
alembic revision --autogenerate -m "migration name"
```

### Применить миграции

```bash
alembic upgrade head
```

### Откатить миграцию

```bash
alembic downgrade -1
```

### Запустить тесты

```bash
docker exec api python -m pytest /usr/src/tests/ -v
```

### Диаграмма БД

```bash
docker exec -ti api eralchemy2 -i postgresql://admin:root@db:5432/robofactory -o diagram.png --exclude-tables alembic_version
```
