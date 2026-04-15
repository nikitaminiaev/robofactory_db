import pytest
from uuid import UUID, uuid4
from unittest.mock import MagicMock, patch
from repository.role_repository import RoleRepository
from models.associations import module_role_assignment


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


class TestRoleRepositoryModuleAssignment:
    """Тесты для методов назначения ролей модулям"""

    @patch('repository.base_repository.Db_session')
    def test_add_role_to_module_success(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_execute_result = MagicMock()
        mock_execute_result.first.return_value = None
        mock_db.execute.return_value = mock_execute_result

        repo = RoleRepository()
        module_id = uuid4()
        role_id = uuid4()
        repo.add_role_to_module(mock_db, module_id, role_id)

        assert mock_db.execute.call_count >= 1
        mock_db.flush.assert_called_once()

    @patch('repository.base_repository.Db_session')
    def test_add_role_to_module_already_exists(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_existing = MagicMock()
        mock_existing.module_id = uuid4()
        mock_existing.role_id = uuid4()
        mock_db.execute.return_value.first.return_value = mock_existing

        repo = RoleRepository()
        module_id = uuid4()
        role_id = uuid4()
        repo.add_role_to_module(mock_db, module_id, role_id)

        mock_db.execute.assert_called_once()
        mock_db.flush.assert_not_called()

    @patch('repository.base_repository.Db_session')
    def test_remove_role_from_module(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        repo = RoleRepository()
        module_id = uuid4()
        role_id = uuid4()
        repo.remove_role_from_module(mock_db, module_id, role_id)

        mock_db.execute.assert_called_once()
        mock_db.flush.assert_called_once()

    @patch('repository.base_repository.Db_session')
    def test_get_module_roles_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_module = MagicMock()
        mock_role = MagicMock()
        mock_role.id = uuid4()
        mock_role.name = "parent"
        mock_module.roles = [mock_role]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_module

        repo = RoleRepository()
        module_id = uuid4()
        result = repo.get_module_roles(mock_db, module_id)

        assert len(result) == 1
        assert result[0].name == "parent"

    @patch('repository.base_repository.Db_session')
    def test_get_module_roles_not_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        repo = RoleRepository()
        module_id = uuid4()
        result = repo.get_module_roles(mock_db, module_id)

        assert result == []

    @patch('repository.base_repository.Db_session')
    def test_fetch_module_roles(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_role = MagicMock()
        mock_role.id = uuid4()
        mock_role.name = "child"
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(roles=[mock_role])

        repo = RoleRepository()
        module_id = uuid4()
        result = repo.fetch_module_roles(module_id)

        assert len(result) == 1

    @patch('repository.base_repository.Db_session')
    def test_assign_role(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        repo = RoleRepository()
        module_id = uuid4()
        role_id = uuid4()
        repo.assign_role(module_id, role_id)

        mock_db.commit.assert_called_once()

    @patch('repository.base_repository.Db_session')
    def test_unassign_role(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        repo = RoleRepository()
        module_id = uuid4()
        role_id = uuid4()
        repo.unassign_role(module_id, role_id)

        mock_db.commit.assert_called_once()

    @patch('repository.base_repository.Db_session')
    def test_create_and_assign_role_new(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_role = MagicMock()
        mock_role.id = uuid4()
        mock_role.name = "new_role"
        mock_role.description = "New role"
        
        def mock_add(obj):
            return obj
        
        mock_db.add.side_effect = mock_add

        repo = RoleRepository()
        module_id = uuid4()
        result = repo.create_and_assign_role(module_id, "new_role", "New role")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('repository.base_repository.Db_session')
    def test_create_and_assign_role_existing(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        existing_role = MagicMock()
        existing_role.id = uuid4()
        existing_role.name = "existing_role"
        mock_db.query.return_value.filter.return_value.first.return_value = existing_role

        repo = RoleRepository()
        module_id = uuid4()
        result = repo.create_and_assign_role(module_id, "existing_role", "Description")

        assert result == existing_role
        mock_db.add.assert_not_called()
