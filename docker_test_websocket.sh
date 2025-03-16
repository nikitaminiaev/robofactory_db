#!/bin/bash

# Скрипт для тестирования WebSocket API внутри Docker-контейнера

# Проверяем, запущен ли контейнер API
CONTAINER_ID=$(docker ps | grep robofactory_db-api | awk '{print $1}')

if [ -z "$CONTAINER_ID" ]; then
    echo "Контейнер API не запущен!"
    exit 1
fi

echo "Найден контейнер API: $CONTAINER_ID"

# Функция для выполнения Python-запроса внутри контейнера
run_python_request() {
    METHOD=$1
    URL=$2
    echo "Выполнение $METHOD запроса к $URL..."
    
    PYTHON_CODE="
import urllib.request
import json

try:
    if '${METHOD}' == 'get':
        req = urllib.request.Request('${URL}', method='GET')
    else:
        req = urllib.request.Request('${URL}', method='POST')
    
    with urllib.request.urlopen(req) as response:
        data = response.read().decode('utf-8')
        try:
            json_data = json.loads(data)
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
        except:
            print(data)
except Exception as e:
    print(f'Ошибка: {str(e)}')
"
    
    docker exec -i $CONTAINER_ID python -c "$PYTHON_CODE"
    echo "Запрос выполнен"
    echo "----------------------------------------"
}

# Проверка статуса WebSocket сервера
check_status() {
    echo "Проверка статуса WebSocket сервера..."
    run_python_request "get" "http://localhost:8000/api/websocket/status"
}

# Запуск WebSocket сервера
start_server() {
    echo "Запуск WebSocket сервера..."
    run_python_request "post" "http://localhost:8000/api/websocket/start"
}

# Остановка WebSocket сервера
stop_server() {
    echo "Остановка WebSocket сервера..."
    run_python_request "post" "http://localhost:8000/api/websocket/stop"
}

# Получение информации о клиентах
get_clients() {
    echo "Получение информации о клиентах..."
    run_python_request "get" "http://localhost:8000/api/websocket/clients"
}

# Получение истории сообщений
get_messages() {
    echo "Получение истории сообщений..."
    run_python_request "get" "http://localhost:8000/api/websocket/messages"
}

# Полное тестирование
run_full_test() {
    echo "Запуск полного тестирования WebSocket API..."
    echo "----------------------------------------"
    
    # Проверяем текущий статус
    check_status
    
    # Останавливаем сервер, если он запущен
    stop_server
    sleep 2
    
    # Запускаем сервер
    start_server
    sleep 2
    
    # Проверяем статус после запуска
    check_status
    
    # Получаем информацию о клиентах
    get_clients
    
    # Получаем историю сообщений
    get_messages
    
    echo "Тестирование завершено"
    echo "----------------------------------------"
}

# Проверяем аргументы командной строки
if [ $# -eq 0 ]; then
    run_full_test
else
    case "$1" in
        status)
            check_status
            ;;
        start)
            start_server
            ;;
        stop)
            stop_server
            ;;
        clients)
            get_clients
            ;;
        messages)
            get_messages
            ;;
        test)
            run_full_test
            ;;
        *)
            echo "Неизвестная команда: $1"
            echo "Доступные команды: status, start, stop, clients, messages, test"
            exit 1
            ;;
    esac
fi

exit 0 