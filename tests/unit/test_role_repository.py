import pytest
from uuid import UUID
from unittest.mock import MagicMock, patch
from repository.role_repository import RoleRepository


class TestRoleRepository:

    @patch('repository.base_repository.Db_session')
    def test_get_role_by_name_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_role = MagicMock()
        mock_role.name = "parent"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_role

        repo = RoleRepository()
        result = repo.get_role_by_name(mock_db, "parent")

        assert result == mock_role
        mock_db.query.assert_called_once()

    @patch('repository.base_repository.Db_session')
    def test_get_role_by_name_not_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        repo = RoleRepository()
        result = repo.get_role_by_name(mock_db, "nonexistent")

        assert result is None

    @patch('repository.base_repository.Db_session')
    def test_create_role(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_role = MagicMock()
        mock_db.add.return_value = mock_role

        repo = RoleRepository()
        result = repo.create_role(mock_db, "test_role", "Test description")

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert result.name == "test_role"
        assert result.description == "Test description"

    @patch('repository.base_repository.Db_session')
    def test_get_or_create_role_existing(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_existing_role = MagicMock()
        mock_existing_role.name = "existing_role"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_role

        repo = RoleRepository()
        result = repo.get_or_create_role(mock_db, "existing_role", "Description")

        mock_db.add.assert_not_called()
        assert result == mock_existing_role

    @patch('repository.base_repository.Db_session')
    def test_get_or_create_role_new(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_new_role = MagicMock()
        mock_db.add.return_value = mock_new_role

        repo = RoleRepository()
        result = repo.get_or_create_role(mock_db, "new_role", "New description")

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert result.name == "new_role"
