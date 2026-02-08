import pytest
from uuid import UUID
from unittest.mock import Mock, patch, MagicMock
from service.brep_storage import create_module_brep_directory, save_brep_file
from pathlib import Path


class TestBrepStorage:

    @patch('service.brep_storage.Path')
    def test_create_module_brep_directory_success(self, mock_path_class):
        # Setup mocks
        mock_base_path = MagicMock()
        mock_module_path = MagicMock()
        mock_path_class.return_value = mock_base_path
        mock_base_path.__truediv__.return_value = mock_module_path
        mock_module_path.mkdir.return_value = None
        mock_module_path.__str__.return_value = '/path/to/module'
        
        # Call function
        result = create_module_brep_directory(UUID('12345678-1234-5678-1234-567812345678'))
        
        # Assertions
        assert result == '/path/to/module'
        mock_path_class.assert_called_once_with('api/resources/brep_files')  # Assuming BREP_FILES_PATH
        mock_base_path.__truediv__.assert_called_once_with('12345678-1234-5678-1234-567812345678')
        mock_module_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch('service.brep_storage.Path')
    def test_create_module_brep_directory_os_error(self, mock_path_class):
        # Setup mocks to raise OSError
        mock_base_path = MagicMock()
        mock_module_path = MagicMock()
        mock_path_class.return_value = mock_base_path
        mock_base_path.__truediv__.return_value = mock_module_path
        mock_module_path.mkdir.side_effect = OSError("Permission denied")
        
        # Call and expect error
        with pytest.raises(OSError, match="Не удалось создать директорию"):
            create_module_brep_directory(UUID('12345678-1234-5678-1234-567812345678'))

    @patch('service.brep_storage.Path')
    def test_save_brep_file_success(self, mock_path_class):
        # Setup mocks
        mock_base_path = MagicMock()
        mock_module_path = MagicMock()
        mock_file_path = MagicMock()
        mock_path_class.return_value = mock_base_path
        mock_base_path.__truediv__.return_value = mock_module_path
        mock_module_path.__truediv__.return_value = mock_file_path
        mock_file_path.write_bytes.return_value = None
        
        # Call function
        result = save_brep_file(
            UUID('12345678-1234-5678-1234-567812345678'),
            'test.brep',
            b'file content'
        )
        
        # Assertions
        assert result == '12345678-1234-5678-1234-567812345678/test.brep'
        mock_path_class.assert_called_once_with('api/resources/brep_files')
        mock_base_path.__truediv__.assert_called_once_with('12345678-1234-5678-1234-567812345678')
        mock_module_path.__truediv__.assert_called_once_with('test.brep')
        mock_file_path.write_bytes.assert_called_once_with(b'file content')

    @patch('service.brep_storage.Path')
    def test_save_brep_file_os_error(self, mock_path_class):
        # Setup mocks to raise OSError
        mock_base_path = MagicMock()
        mock_module_path = MagicMock()
        mock_file_path = MagicMock()
        mock_path_class.return_value = mock_base_path
        mock_base_path.__truediv__.return_value = mock_module_path
        mock_module_path.__truediv__.return_value = mock_file_path
        mock_file_path.write_bytes.side_effect = OSError("Write failed")
        
        # Call and expect error
        with pytest.raises(OSError, match="Не удалось сохранить файл"):
            save_brep_file(
                UUID('12345678-1234-5678-1234-567812345678'),
                'test.brep',
                b'file content'
            )