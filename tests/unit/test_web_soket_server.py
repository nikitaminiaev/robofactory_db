import pytest
from unittest.mock import Mock, patch, MagicMock
from service.web_soket_server import WebSocketServer, get_server_instance, get_connected_clients_count


class TestWebSocketServer:

    @patch('service.web_soket_server.threading.Lock')
    def test_singleton_instance(self, mock_lock):
        # Test that multiple calls return the same instance
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        
        instance1 = WebSocketServer()
        instance2 = WebSocketServer()
        
        assert instance1 is instance2

    @patch('service.web_soket_server.threading.Lock')
    def test_init_not_initialized(self, mock_lock):
        # Test __init__ when not initialized
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        
        instance = WebSocketServer(host="127.0.0.1", port=9999)
        
        assert instance.host == "127.0.0.1"
        assert instance.port == 9999
        assert instance._initialized is True

    @patch('service.web_soket_server.threading.Lock')
    def test_get_connected_clients_count(self, mock_lock):
        # Test get_connected_clients_count
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        
        instance = WebSocketServer()
        instance.connected_clients = [MagicMock(), MagicMock()]
        instance.connected_clients_info = [('127.0.0.1', 1234), ('127.0.0.2', 5678)]
        
        result = instance.get_connected_clients_count()
        
        assert result['count'] == 2
        assert len(result['clients']) == 2

    @patch('service.web_soket_server.socket')
    @patch('service.web_soket_server.threading.Lock')
    def test_is_running_server_valid(self, mock_lock, mock_socket):
        # Test is_running when server is valid
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        
        mock_server_socket = MagicMock()
        mock_server_socket.fileno.return_value = 5  # Valid file descriptor
        
        instance = WebSocketServer()
        instance.server = mock_server_socket
        
        result = instance.is_running()
        
        assert result is True

    @patch('service.web_soket_server.socket')
    @patch('service.web_soket_server.threading.Lock')
    def test_is_running_server_invalid(self, mock_lock, mock_socket):
        # Test is_running when server fileno invalid
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        
        mock_server_socket = MagicMock()
        mock_server_socket.fileno.return_value = -1  # Invalid
        
        instance = WebSocketServer()
        instance.server = mock_server_socket
        
        result = instance.is_running()
        
        assert result is False

    @patch('service.web_soket_server.socket')
    @patch('service.web_soket_server.threading.Lock')
    def test_is_running_connect_success(self, mock_lock, mock_socket):
        # Test is_running by connecting to external host
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        
        mock_sock_instance = MagicMock()
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None  # Success
        
        instance = WebSocketServer()
        instance.server = None
        
        result = instance.is_running(host="127.0.0.1", port=8080)
        
        assert result is True
        mock_sock_instance.connect.assert_called_once_with(("127.0.0.1", 8080))

    @patch('service.web_soket_server.socket')
    @patch('service.web_soket_server.threading.Lock')
    def test_is_running_connect_fail(self, mock_lock, mock_socket):
        # Test is_running connect failure
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        
        mock_sock_instance = MagicMock()
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.connect.side_effect = ConnectionRefusedError
        
        instance = WebSocketServer()
        instance.server = None
        
        result = instance.is_running(host="127.0.0.1", port=8080)
        
        assert result is False

    @patch('service.web_soket_server.socket')
    @patch('service.web_soket_server.threading.Lock')
    def test_send_message_success(self, mock_lock, mock_socket):
        # Test send_message success
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        
        mock_sock_instance = MagicMock()
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None
        mock_sock_instance.recv.return_value = b"OK"  # Server response
        
        instance = WebSocketServer()
        
        result = instance.send_message("test message", host="127.0.0.1", port=8080)
        
        assert result is True
        mock_sock_instance.sendall.assert_called()

    @patch('service.web_soket_server.socket')
    @patch('service.web_soket_server.threading.Lock')
    def test_send_message_connection_refused(self, mock_lock, mock_socket):
        # Test send_message connection refused
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        
        mock_sock_instance = MagicMock()
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.connect.side_effect = ConnectionRefusedError
        
        instance = WebSocketServer()
        
        result = instance.send_message("test message", host="127.0.0.1", port=8080)
        
        assert result is False

    @patch('service.web_soket_server.threading.Lock')
    def test_get_server_instance(self, mock_lock):
        # Test get_server_instance function
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        
        instance = get_server_instance(host="127.0.0.1", port=9999)
        
        assert isinstance(instance, WebSocketServer)
        assert instance.host == "127.0.0.1"
        assert instance.port == 9999

    @patch('service.web_soket_server.threading.Lock')
    def test_get_connected_clients_count_function(self, mock_lock):
        # Test get_connected_clients_count function
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        
        instance = get_server_instance()
        instance.connected_clients = [MagicMock()]
        instance.connected_clients_info = [('127.0.0.1', 1234)]
        
        result = get_connected_clients_count()
        
        assert result['count'] == 1