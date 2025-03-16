import socket
import base64
import hashlib
import threading
import struct  
import json

def _handle_client(client_socket, addr):
    print(f"Подключение от {addr}")
    
    # Получение данных от клиента
    request = client_socket.recv(1024)
    
    # Проверяем, является ли это HTTP-запросом для WebSocket handshake
    if request.startswith(b'GET '):
        # Это WebSocket handshake
        request_text = request.decode('utf-8')
        
        # Извлечение ключа из заголовка
        key = None
        for line in request_text.split('\r\n'):
            if "Sec-WebSocket-Key" in line:
                key = line.split(': ')[1]
                break
        
        if not key:
            print("Ключ WebSocket не найден")
            client_socket.close()
            return
        
        # Вычисление ответного ключа согласно протоколу WebSocket
        magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        accept_key = base64.b64encode(
            hashlib.sha1((key + magic_string).encode()).digest()
        ).decode('utf-8')
        
        # Отправка ответа handshake
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_key}\r\n"
            "\r\n"
        )
        client_socket.sendall(response.encode())
        
        # Обработка WebSocket-соединения
        _handle_websocket_connection(client_socket, addr)
    else:
        # Это простое сообщение без WebSocket-протокола
        try:
            message = request.decode('utf-8')
            print(f"Получено простое сообщение от {addr}: {message}")
            
            # Проверяем, является ли сообщение JSON-объектом
            try:
                json_data = json.loads(message)
                print(f"Получен JSON-объект: {json_data}")
                
                # Транслируем сообщение всем подключенным WebSocket-клиентам
                _broadcast_message(message)
                
                # Если это команда для FreeCad, можно добавить специальную обработку
                if isinstance(json_data, dict) and json_data.get("type") == "freecad_command":
                    print(f"Получена команда для FreeCad: {json_data.get('python_code', '')}")
            except json.JSONDecodeError:
                # Если сообщение не является JSON, проверяем, является ли оно строкой "hello"
                if message == "hello":
                    _broadcast_message("hello")
                
            # Отправляем подтверждение
            client_socket.sendall(b"OK")
        except Exception as e:
            print(f"Ошибка при обработке простого сообщения: {e}")
        finally:
            client_socket.close()

def _handle_websocket_connection(client_socket, addr):
    """Обрабатывает WebSocket-соединение после успешного handshake"""
    try:
        # Добавляем клиента в список подключенных клиентов
        connected_clients.append(client_socket)
        client_info = (addr[0], addr[1])
        connected_clients_info.append(client_info)
        print(f"WebSocket-клиент {addr} добавлен. Всего клиентов: {len(connected_clients)}")
        
        # Функция отправки сообщения клиенту
        def send_message(message):
           if isinstance(message, str):
               message = message.encode('utf-8')

           # Сервер не должен маскировать данные
           length = len(message)

           if length < 126:
               header = struct.pack('!BB', 0x81, length)
           elif length < 65536:
               header = struct.pack('!BBH', 0x81, 126, length)
           else:
               header = struct.pack('!BBQ', 0x81, 127, length)

           client_socket.sendall(header + message)
            
        def receive_message():
           header = client_socket.recv(2)
           if not header:
               return None

           has_mask = (header[1] & 0x80) != 0
           length = header[1] & 0x7F

           # Получение расширенной длины
           if length == 126:
               length_bytes = client_socket.recv(2)
               length = struct.unpack('!H', length_bytes)[0]
           elif length == 127:
               length_bytes = client_socket.recv(8)
               length = struct.unpack('!Q', length_bytes)[0]

           # Получение маски (клиенты всегда должны маскировать данные)
           mask = None
           if has_mask:
               mask = client_socket.recv(4)

           # Получение данных
           payload = bytearray()
           remaining = length
           while remaining > 0:
               chunk = client_socket.recv(min(remaining, 4096))
               if not chunk:
                   break
               payload.extend(chunk)
               remaining -= len(chunk)

           # Демаскирование данных
           if has_mask and mask:
               for i in range(len(payload)):
                   payload[i] ^= mask[i % 4]

           # Декодирование с обработкой ошибок
           try:
               return payload.decode('utf-8')
           except UnicodeDecodeError:
               print("Ошибка декодирования UTF-8")
               return None    
        
        # Основной цикл обработки сообщений
        while True:
            message = receive_message()
            if message is None:
                break
                
            print(f"Получено от WebSocket-клиента {addr}: {message}")
            
            # Отправка ответа
            response_message = f"Сервер получил: {message}"
            send_message(response_message)
            
    except Exception as e:
        print(f"Ошибка при обработке WebSocket-сообщений: {e}")
    finally:
        # Удаляем клиента из списка подключенных клиентов
        if client_socket in connected_clients:
            index = connected_clients.index(client_socket)
            connected_clients.remove(client_socket)
            if index < len(connected_clients_info):
                connected_clients_info.pop(index)
            print(f"WebSocket-клиент {addr} удален. Осталось клиентов: {len(connected_clients)}")
        client_socket.close()
        print(f"Соединение с {addr} закрыто")

def _broadcast_message(message):
    """Отправляет сообщение всем подключенным WebSocket-клиентам"""
    if not connected_clients:
        print("Нет подключенных WebSocket-клиентов для отправки сообщения")
        return
    
    print(f"Отправка сообщения '{message}' всем {len(connected_clients)} клиентам")
    
    # Преобразуем сообщение в байты, если оно строка
    if isinstance(message, str):
        message = message.encode('utf-8')
    
    # Формируем WebSocket-фрейм
    length = len(message)
    if length < 126:
        header = struct.pack('!BB', 0x81, length)
    elif length < 65536:
        header = struct.pack('!BBH', 0x81, 126, length)
    else:
        header = struct.pack('!BBQ', 0x81, 127, length)
    
    frame = header + message
    
    # Отправляем сообщение всем клиентам
    disconnected_clients = []
    for client in connected_clients:
        try:
            client.sendall(frame)
            print(f"Сообщение успешно отправлено клиенту")
        except Exception as e:
            print(f"Ошибка при отправке сообщения клиенту: {e}")
            disconnected_clients.append(client)
    
    # Удаляем отключенных клиентов
    for client in disconnected_clients:
        if client in connected_clients:
            connected_clients.remove(client)
    
    if disconnected_clients:
        print(f"Удалено {len(disconnected_clients)} отключенных клиентов. Осталось: {len(connected_clients)}")

# Глобальный список подключенных WebSocket-клиентов
connected_clients = []
connected_clients_info = []  # Список с информацией о клиентах (адрес, порт)

def get_connected_clients_count():
    """Возвращает количество подключенных клиентов и информацию о них"""
    return {
        "count": len(connected_clients),
        "clients": connected_clients_info
    }

def is_socket_server_running(host="localhost", port=8765):
    """Проверяет, запущен ли WebSocket-сервер"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = False
    try:
        # Пытаемся подключиться к серверу
        sock.connect((host, port))
        result = True
    except (socket.timeout, ConnectionRefusedError):
        result = False
    finally:
        sock.close()
    return result

def send_message_to_websocket(message, host="localhost", port=8765):
    """Отправляет сообщение через WebSocket-сервер"""
    try:
        # Создаем простой клиент для отправки сообщения
        # Это упрощенная реализация, в реальном приложении 
        # следует использовать полноценную библиотеку для WebSocket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        # Отправляем сообщение через WebSocket-сервер
        # Здесь мы просто передаем сообщение серверу, который сам обработает его
        # и отправит подключенным клиентам
        print(f"Отправка сообщения на WebSocket-сервер: {message}")
        sock.sendall(message.encode('utf-8'))
        
        # Ожидаем подтверждение от сервера
        response = sock.recv(1024)
        print(f"Получен ответ от WebSocket-сервера: {response.decode('utf-8')}")
        
        sock.close()
        return True
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
        return False

def start_server(host="0.0.0.0", port=8765):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    
    print(f"Сервер запущен на {host}:{port}")
    
    try:
        while True:
            client_sock, addr = server.accept()
            client_thread = threading.Thread(
                target=_handle_client,
                args=(client_sock, addr)
            )
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("Сервер остановлен")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()