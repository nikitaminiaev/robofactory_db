#!/usr/bin/env python3
"""
Скрипт для тестирования API веб-сокет сервера
"""

import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000"  # Измените на ваш базовый URL

def print_separator():
    print("-" * 80)

def check_server_status():
    """Проверяет статус веб-сокет сервера"""
    print("Проверка статуса сервера...")
    try:
        response = requests.get(f"{BASE_URL}/api/websocket/status")
        data = response.json()
        print(f"Статус сервера: {'Запущен' if data.get('running') else 'Остановлен'}")
        return data.get('running', False)
    except Exception as e:
        print(f"Ошибка при проверке статуса сервера: {e}")
        return False

def start_server():
    """Запускает веб-сокет сервер"""
    print("Запуск сервера...")
    try:
        response = requests.post(f"{BASE_URL}/api/websocket/start")
        data = response.json()
        print(f"Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get('success', False)
    except Exception as e:
        print(f"Ошибка при запуске сервера: {e}")
        return False

def stop_server():
    """Останавливает веб-сокет сервер"""
    print("Остановка сервера...")
    try:
        response = requests.post(f"{BASE_URL}/api/websocket/stop")
        data = response.json()
        print(f"Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get('success', False)
    except Exception as e:
        print(f"Ошибка при остановке сервера: {e}")
        return False

def get_clients():
    """Получает информацию о подключенных клиентах"""
    print("Получение информации о клиентах...")
    try:
        response = requests.get(f"{BASE_URL}/api/websocket/clients")
        data = response.json()
        print(f"Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    except Exception as e:
        print(f"Ошибка при получении информации о клиентах: {e}")
        return None

def get_messages():
    """Получает историю сообщений"""
    print("Получение истории сообщений...")
    try:
        response = requests.get(f"{BASE_URL}/api/websocket/messages")
        data = response.json()
        print(f"Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    except Exception as e:
        print(f"Ошибка при получении истории сообщений: {e}")
        return None

def run_full_test():
    """Запускает полное тестирование API"""
    print_separator()
    print("Начало полного тестирования API веб-сокет сервера")
    print_separator()
    
    # Проверяем текущий статус
    initial_status = check_server_status()
    print_separator()
    
    if initial_status:
        print("Сервер уже запущен, останавливаем его для чистого теста")
        stop_server()
        print_separator()
        time.sleep(2)
    
    # Запускаем сервер
    start_success = start_server()
    print_separator()
    time.sleep(2)
    
    if not start_success:
        print("Не удалось запустить сервер, повторная попытка...")
        start_success = start_server()
        print_separator()
        time.sleep(2)
    
    # Проверяем статус после запуска
    status_after_start = check_server_status()
    print_separator()
    
    if not status_after_start:
        print("Сервер не запустился после команды запуска!")
    
    # Получаем информацию о клиентах
    clients_info = get_clients()
    print_separator()
    
    # Получаем историю сообщений
    messages_info = get_messages()
    print_separator()
    
    # Останавливаем сервер
    stop_success = stop_server()
    print_separator()
    time.sleep(2)
    
    # Проверяем статус после остановки
    status_after_stop = check_server_status()
    print_separator()
    
    if status_after_stop:
        print("Сервер не остановился после команды остановки!")
    
    print("Тестирование завершено")
    print_separator()

def main():
    """Основная функция"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "status":
            check_server_status()
        elif command == "start":
            start_server()
        elif command == "stop":
            stop_server()
        elif command == "clients":
            get_clients()
        elif command == "messages":
            get_messages()
        elif command == "test":
            run_full_test()
        else:
            print(f"Неизвестная команда: {command}")
            print("Доступные команды: status, start, stop, clients, messages, test")
    else:
        run_full_test()

if __name__ == "__main__":
    main() 