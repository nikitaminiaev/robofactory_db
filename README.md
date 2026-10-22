# RoboFactory DB

PLM-база для хранения модулей робототехники: FastAPI + PostgreSQL (docker compose), web-интерфейс, интеграция с FreeCAD (плагин PLMplugin).

---

## Установка для клиента (основной способ): AppImage

Приложение распространяется как самодостаточный `AppImage` — от клиента требуется только Docker, ничего из репозитория клонировать не нужно.

### Требования

- Linux x86_64
- **Docker + плагин docker compose** (`docker compose version` должен работать; доступ без `sudo`: `sudo usermod -aG docker $USER` и перелогин)
- Опционально: FreeCAD (для плагина PLMplugin)

### Сборка AppImage (на машине разработчика)

```bash
./packaging/build_appimage.sh        # результат: dist/RoboFactory-DB-x86_64.AppImage
```

Зависимости сборки: `bash`, `rsync`, `curl` (Docker не нужен).
Плагин берётся из смежного репозитория; путь можно переопределить:

```bash
PLMPLUGIN_SRC=/путь/до/PLMplugin ./packaging/build_appimage.sh
```

### Запуск у клиента

```bash
chmod +x RoboFactory-DB-x86_64.AppImage
./RoboFactory-DB-x86_64.AppImage
```

Первый запуск: разворачивает приложение, собирает docker-образы (несколько минут), применяет миграции БД, открывает web-интерфейс. При запуске двойным кликом приложение уходит в фон, а на экране показывается окно прогресса (`zenity`/`kdialog`/`yad`; если их нет — только уведомление). Журнал: `~/.local/share/robofactory-db/logs/app.log`.

Повторный запуск безопасен: при параллельном запуске второй процесс не трогает docker, а показывает окно «уже запускается/работает» и открывает web-интерфейс.

Web-интерфейс: http://localhost:18000 (точный адрес печатается при запуске и виден в `--status`)

Если не хватает `libfuse2`:
```bash
./RoboFactory-DB-x86_64.AppImage --appimage-extract-and-run start
```

### Команды

```
(без аргументов) | start   — запуск сервисов + открытие браузера
--no-browser               — запуск без открытия браузера
--gui | --no-gui           — принудительно вкл/выкл окно прогресса
--stop                     — остановка сервисов
--status                   — статус: версия, контейнеры, доступность API
--update-plugin            — переустановка/обновление PLMplugin в FreeCAD
--uninstall                — удаление сервисов (спросит про каталог данных)
```

### Где живут данные

```
~/.local/share/robofactory-db/
  app/             — код приложения (обновляется при смене версии AppImage)
  data/storage/    — том PostgreSQL
  data/resources/  — BREP-файлы и git-репозитории модулей
  logs/app.log     — журнал запусков
  plugin-backups/  — бэкапы плагина (последние 3)
```

Удаление этого каталога = полный сброс приложения.

### Порты

Дефолты нестандартные, чтобы не конфликтовать с dev-стеком и другими сервисами. Настраиваются в `~/.local/share/robofactory-db/app/.env`:

```
RF_API_PORT=18000   # web-интерфейс
RF_DB_PORT=15433    # PostgreSQL (хост-машина)
RF_WS_PORT=18765    # WebSocket-сервер FreeCAD (читает и плагин PLMplugin)
```

Если порт занят, при запуске приложение автоматически подбирает свободный (в диапазоне +200 вверх) и сохраняет его в `.env` — ручное вмешательство не требуется. Точные порты печатаются при запуске и в `--status`.

Ручное изменение: правка `.env`, затем `./RoboFactory-DB-x86_64.AppImage --stop` и запуск заново.

### Интеграция с FreeCAD

При каждом запуске плагин PLMplugin автоматически устанавливается в найденный каталог FreeCAD (`~/.local/share/FreeCAD/Mod` и т.п.). Если FreeCAD не найден:

```bash
FREECAD_MOD_DIR=/путь/до/FreeCAD/Mod ./RoboFactory-DB-x86_64.AppImage start
```

Если каталог плагина принадлежит `root` (например, FreeCAD когда-то запускался через `sudo`), установка плагина не удаётся — приложение всё равно запускается, но выводит предупреждение. Исправляется так:

```bash
sudo chown -R $USER ~/.local/share/FreeCAD/Mod
./RoboFactory-DB-x86_64.AppImage --update-plugin
```

### Устранение неполадок docker

Перед запуском контейнеров приложение само убирает «осиротевшие» контейнеры `rf-app-db`/`rf-app-api` и дубликаты сети `robofactory-app_default`, оставшиеся от прошлых (в том числе параллельных) запусков. Если всё равно возникает ошибка вида `container name "/rf-app-db" is already in use` или `network robofactory-app_default is ambiguous`, выполните вручную:

```bash
docker rm -f rf-app-db rf-app-api
docker network ls --filter name=robofactory-app_default -q | xargs -r docker network rm
```

### Обновление

Клиенту достаточно положить новый AppImage на место старого и запустить — код и плагин обновятся сами, данные в `~/.local/share/robofactory-db/` сохранятся.

### Удаление

```bash
# удалить сервисы, но сохранить данные (БД, BREP, git-репозитории модулей)
./RoboFactory-DB-x86_64.AppImage --uninstall --keep-data

# удалить всё вместе с данными (спрашивать не будет)
./RoboFactory-DB-x86_64.AppImage --uninstall --purge

# без флагов — спросит в окне/в терминале, удалять ли каталог данных
./RoboFactory-DB-x86_64.AppImage --uninstall
```

`--uninstall` удаляет контейнеры и сеть приложения, docker-образ `robofactory-app-api`, бэкапы плагина и сам PLMplugin из FreeCAD (только если он был установлен приложением — есть маркер `.rf-version`). Данные (`~/.local/share/robofactory-db/`, включая базу PostgreSQL и BREP-файлы) удаляются только с `--purge` или по подтверждению. Файл самого AppImage нужно удалить вручную.

---

## Разработка

```bash
./install.sh   # первый запуск: создаёт .env, собирает и запускает контейнеры
./start.sh     # последующие запуски
```

После запуска:
- API: http://localhost:8000
- DB:  localhost:5433

Остановить:

    docker compose down

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