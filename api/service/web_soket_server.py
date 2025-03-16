import socket
import base64
import hashlib
import threading
import struct  
import json

class WebSocketServer:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WebSocketServer, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, host="0.0.0.0", port=8765):
        if self._initialized:
            return
            
        self.host = host
        self.port = port
        self.server = None
        self.connected_clients = []
        self.connected_clients_info = []
        self._initialized = True
    
    def _handle_client(self, client_socket, addr):
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
            self._handle_websocket_connection(client_socket, addr)
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
                    self._broadcast_message(message)
                    
                    # Если это команда для FreeCad, можно добавить специальную обработку
                    if isinstance(json_data, dict) and json_data.get("type") == "freecad_command":
                        print(f"Получена команда для FreeCad: {json_data.get('python_code', '')}")
                except json.JSONDecodeError:
                    # Если сообщение не является JSON, проверяем, является ли оно строкой "hello"
                    if message == "hello":
                        self._broadcast_message("hello")
                    
                # Отправляем подтверждение
                client_socket.sendall(b"OK")
            except Exception as e:
                print(f"Ошибка при обработке простого сообщения: {e}")
            finally:
                client_socket.close()

    def _handle_websocket_connection(self, client_socket, addr):
        """Обрабатывает WebSocket-соединение после успешного handshake"""
        try:
            # Добавляем клиента в список подключенных клиентов
            self.connected_clients.append(client_socket)
            client_info = (addr[0], addr[1])
            self.connected_clients_info.append(client_info)
            print(f"WebSocket-клиент {addr} добавлен. Всего клиентов: {len(self.connected_clients)}")
            
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
            if client_socket in self.connected_clients:
                index = self.connected_clients.index(client_socket)
                self.connected_clients.remove(client_socket)
                if index < len(self.connected_clients_info):
                    self.connected_clients_info.pop(index)
                print(f"WebSocket-клиент {addr} удален. Осталось клиентов: {len(self.connected_clients)}")
            client_socket.close()
            print(f"Соединение с {addr} закрыто")

    def _broadcast_message(self, message):
        """Отправляет сообщение всем подключенным WebSocket-клиентам"""
        if not self.connected_clients:
            print("Нет подключенных WebSocket-клиентов для отправки сообщения")
            return
        
        print(f"Отправка сообщения '{message}' всем {len(self.connected_clients)} клиентам")
        
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
        for client in self.connected_clients:
            try:
                client.sendall(frame)
                print(f"Сообщение успешно отправлено клиенту")
            except Exception as e:
                print(f"Ошибка при отправке сообщения клиенту: {e}")
                disconnected_clients.append(client)
        
        # Удаляем отключенных клиентов
        for client in disconnected_clients:
            if client in self.connected_clients:
                self.connected_clients.remove(client)
        
        if disconnected_clients:
            print(f"Удалено {len(disconnected_clients)} отключенных клиентов. Осталось: {len(self.connected_clients)}")

    def get_connected_clients_count(self):
        """Возвращает количество подключенных клиентов и информацию о них"""
        return {
            "count": len(self.connected_clients),
            "clients": self.connected_clients_info
        }

    def is_running(self, host="localhost", port=None):
        """Проверяет, запущен ли WebSocket-сервер"""
        # Сначала проверяем локальное состояние сервера
        if self.server is not None and hasattr(self.server, 'fileno'):
            try:
                # Проверяем, действителен ли файловый дескриптор сокета
                if self.server.fileno() != -1:
                    return True
            except OSError:
                # Если возникла ошибка, значит сокет недействителен
                pass
                
        # Затем пытаемся подключиться к серверу
        if port is None:
            port = self.port
            
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = False
        try:
            # Пытаемся подключиться к серверу
            sock.connect((host, port))
            result = True
        except (socket.timeout, ConnectionRefusedError, OSError):
            result = False
        finally:
            try:
                sock.close()
            except Exception:
                pass
        return result

    def send_message(self, message, host="localhost", port=None):
        """Отправляет сообщение через WebSocket-сервер"""
        if port is None:
            port = self.port
        
        print(f"[WebSocketServer] Попытка отправить сообщение на {host}:{port}")
            
        try:
            # Сначала проверяем, запущен ли сервер
            if not self.is_running(host, port):
                print(f"[WebSocketServer] Ошибка: сервер не запущен на {host}:{port}")
                return False
                
            # Создаем простой клиент для отправки сообщения
            print(f"[WebSocketServer] Создание сокета для отправки сообщения")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # Увеличиваем таймаут для более надежного соединения
            
            try:
                print(f"[WebSocketServer] Подключение к {host}:{port}")
                sock.connect((host, port))
                
                # Отправляем сообщение через WebSocket-сервер
                print(f"[WebSocketServer] Отправка сообщения: {message[:100]}{'...' if len(message) > 100 else ''}")
                sock.sendall(message.encode('utf-8'))
                
                # Ожидаем подтверждение от сервера
                print(f"[WebSocketServer] Ожидание ответа от сервера")
                sock.settimeout(10)  # Увеличиваем таймаут для ожидания ответа
                response = sock.recv(1024)
                print(f"[WebSocketServer] Получен ответ от сервера: {response.decode('utf-8')}")
                
                return True
            except socket.timeout:
                print(f"[WebSocketServer] Ошибка: превышено время ожидания при подключении к {host}:{port}")
                return False
            except ConnectionRefusedError:
                print(f"[WebSocketServer] Ошибка: соединение отклонено сервером {host}:{port}")
                return False
            finally:
                try:
                    sock.close()
                    print(f"[WebSocketServer] Сокет закрыт")
                except:
                    pass
                
        except Exception as e:
            print(f"[WebSocketServer] Общая ошибка при отправке сообщения: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start(self):
        """Запускает WebSocket-сервер"""
        if self.server:
            print(f"Сервер уже запущен на {self.host}:{self.port}")
            return

        try:
            # Создаем новый сокет
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Пытаемся привязать сокет к адресу и порту
            try:
                self.server.bind((self.host, self.port))
            except OSError as e:
                print(f"Ошибка при привязке к порту {self.port}: {e}")
                # Порт может быть уже занят, проверяем
                if self.is_running():
                    print(f"Сервер уже запущен на {self.host}:{self.port}, используем существующий")
                    self.server = None
                    return
                raise  # Если порт занят, но сервер не запущен - поднимаем ошибку
                
            self.server.listen(5)
            print(f"Сервер запущен на {self.host}:{self.port}")
            
            while True:
                if self.server is None:
                    print("Сервер был остановлен")
                    break
                    
                try:
                    client_sock, addr = self.server.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_sock, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except OSError as e:
                    print(f"Ошибка при принятии соединения: {e}")
                    # Если сокет закрыт или недействителен
                    if self.server is None:
                        break
                    continue
                    
        except KeyboardInterrupt:
            print("Сервер остановлен по запросу пользователя")
        except Exception as e:
            print(f"Ошибка при запуске сервера: {e}")
        finally:
            self.stop()

    def stop(self):
        """Останавливает WebSocket-сервер"""
        with self._lock:  # Используем блокировку для безопасного завершения
            if self.server:
                try:
                    # Закрываем серверный сокет
                    self.server.close()
                    print("Серверный сокет закрыт")
                except Exception as e:
                    print(f"Ошибка при закрытии серверного сокета: {e}")
                finally:
                    self.server = None
                
            # Закрываем все клиентские соединения
            disconnected_count = 0
            for client in list(self.connected_clients):  # Используем копию списка
                try:
                    client.close()
                    disconnected_count += 1
                except Exception as e:
                    print(f"Ошибка при закрытии клиентского соединения: {e}")
            
            if disconnected_count > 0:
                print(f"Закрыто {disconnected_count} клиентских соединений")
                
            # Очищаем списки
            self.connected_clients = []
            self.connected_clients_info = []
            
            print("Сервер полностью остановлен")

# Функция-синглтон для получения экземпляра WebSocketServer
def get_server_instance(host="0.0.0.0", port=8765):
    """Возвращает экземпляр сервера WebSocket (синглтон)"""
    return WebSocketServer(host, port)

# Для обратной совместимости
def is_socket_server_running(host="localhost", port=8765):
    """Проверяет, запущен ли WebSocket-сервер"""
    return get_server_instance().is_running(host, port)

def get_connected_clients_count():
    """Возвращает количество подключенных клиентов и информацию о них"""
    return get_server_instance().get_connected_clients_count()

def send_message_to_websocket(message, host="localhost", port=8765):
    """Отправляет сообщение через WebSocket-сервер"""
    return get_server_instance().send_message(message, host, port)

def start_server(host="0.0.0.0", port=8765):
    """Запускает WebSocket-сервер"""
    server = get_server_instance(host, port)
    server.start()

if __name__ == "__main__":
    start_server()