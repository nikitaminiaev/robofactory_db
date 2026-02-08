import pytest
from uuid import UUID
from unittest.mock import Mock, MagicMock, patch
from repository.module_repository import ModuleRepository


class TestModuleRepository:

    @patch('repository.base_repository.Db_session')
    def test_delete_module_success(self, mock_db_session_class):
        # Setup mocks
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        
        mock_module = MagicMock()
        mock_module.id = UUID('12345678-1234-5678-1234-567812345678')
        mock_module.bounding_contour = MagicMock()
        
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_module
        
        # Mock the subqueries and deletes
        mock_db.query.return_value.filter.return_value.delete.return_value = None
        mock_db.execute.return_value = None
        
        repo = ModuleRepository()
        
        # Call method
        repo.delete_module(UUID('12345678-1234-5678-1234-567812345678'))
        
        # Assertions
        mock_db.delete.assert_any_call(mock_module.bounding_contour)
        mock_db.delete.assert_any_call(mock_module)
        mock_db.commit.assert_called_once()

    @patch('repository.base_repository.Db_session')
    def test_delete_module_not_found(self, mock_db_session_class):
        # Setup mocks
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        
        repo = ModuleRepository()
        
        # Call and expect error
        with pytest.raises(ValueError, match="Модуль с id .* не найден"):
            repo.delete_module(UUID('12345678-1234-5678-1234-567812345678'))

    @patch('repository.base_repository.Db_session')
    def test_delete_module_no_bounding_contour(self, mock_db_session_class):
        # Setup mocks
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        
        mock_module = MagicMock()
        mock_module.id = UUID('12345678-1234-5678-1234-567812345678')
        mock_module.bounding_contour = None
        
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_module
        
        repo = ModuleRepository()
        
        # Call method
        repo.delete_module(UUID('12345678-1234-5678-1234-567812345678'))
        
        # Assertions - delete not called on bounding_contour
        mock_db.delete.assert_called_once_with(mock_module)
        mock_db.commit.assert_called_once()