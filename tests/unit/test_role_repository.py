import pytest
from types import SimpleNamespace
from uuid import UUID, uuid4
from unittest.mock import MagicMock, patch
from repository.role_repository import RoleRepository
from models import ModuleRole, RolePort
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

        assert mock_db.execute.call_count == 3
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

    @patch('repository.base_repository.Db_session')
    def test_create_role_standalone(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_role = MagicMock()
        mock_role.id = uuid4()
        mock_role.name = "standalone"
        mock_role.description = "Standalone desc"
        mock_role.created_ts = None

        def mock_add(obj):
            obj.name = "standalone"
            obj.description = "Standalone desc"
            obj.id = mock_role.id
            obj.created_ts = None
            return obj

        mock_db.add.side_effect = mock_add

        repo = RoleRepository()
        result = repo.create_role_standalone("standalone", "Standalone desc")

        assert result["name"] == "standalone"
        assert result["description"] == "Standalone desc"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()


class TestRoleRepositoryDetails:
    @patch('repository.base_repository.Db_session')
    def test_get_role_details_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        role_id = uuid4()
        mock_role = MagicMock()
        mock_role.id = role_id
        mock_role.name = "controller"
        mock_role.description = "Main controller"
        mock_role.created_ts = None
        def query_side_effect(model):
            query = MagicMock()
            if model is ModuleRole:
                query.filter.return_value.first.return_value = mock_role
                return query
            if model is RolePort:
                query.filter.return_value.order_by.return_value.all.return_value = []
                return query
            raise AssertionError(f"Unexpected model {model}")

        mock_db.query.side_effect = query_side_effect
        mock_db.execute.return_value.fetchall.return_value = []

        repo = RoleRepository()
        result = repo.get_role_details(role_id)

        assert result["id"] == str(role_id)
        assert result["name"] == "controller"
        assert result["modules"] == []
        assert result["ports"] == []
        assert result["stream_usages"] == []

    @patch('repository.base_repository.Db_session')
    def test_get_role_details_not_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        repo = RoleRepository()
        result = repo.get_role_details(uuid4())

        assert result is None

    @patch('repository.base_repository.Db_session')
    def test_get_role_modules(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        module_id = uuid4()
        mock_db.execute.return_value.fetchall.return_value = [
            SimpleNamespace(id=module_id, name="Module A", description="Description"),
        ]

        repo = RoleRepository()
        result = repo.get_role_modules(mock_db, uuid4())

        assert result == [
            {"id": str(module_id), "name": "Module A", "description": "Description"},
        ]

    @patch('repository.base_repository.Db_session')
    def test_get_role_port_usages(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        link_id = uuid4()
        parent_id = uuid4()
        child_id = uuid4()
        mock_db.execute.return_value.fetchall.return_value = [
            SimpleNamespace(
                parent_child_module_id=link_id,
                parent_id=parent_id,
                parent_name="Parent",
                child_id=child_id,
                child_name="Child",
            ),
        ]

        repo = RoleRepository()
        result = repo.get_role_port_usages(mock_db, uuid4())

        assert result == [
            {
                "parent_child_module_id": str(link_id),
                "parent_id": str(parent_id),
                "parent_name": "Parent",
                "child_id": str(child_id),
                "child_name": "Child",
            },
        ]

    @patch('repository.base_repository.Db_session')
    def test_get_role_stream_usages(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        module_id = uuid4()
        stream_id = uuid4()
        source_role_id = uuid4()
        target_role_id = uuid4()
        mock_db.execute.return_value.fetchall.return_value = [
            SimpleNamespace(
                module_id=module_id,
                module_name="Parent",
                source_role_id=source_role_id,
                source_role_name="Source",
                target_role_id=target_role_id,
                target_role_name="Target",
                source_port_id=None,
                source_port_name=None,
                target_port_id=None,
                target_port_name=None,
                stream_id=stream_id,
                stream_name="Command",
                stream_description="Command stream",
            ),
        ]

        repo = RoleRepository()
        result = repo.get_role_stream_usages(mock_db, source_role_id)

        assert result == [
            {
                "module_id": str(module_id),
                "module_name": "Parent",
                "source_role_id": str(source_role_id),
                "source_role_name": "Source",
                "target_role_id": str(target_role_id),
                "target_role_name": "Target",
                "source_port_id": None,
                "source_port_name": None,
                "target_port_id": None,
                "target_port_name": None,
                "stream_id": str(stream_id),
                "stream_name": "Command",
                "stream_description": "Command stream",
            },
        ]

    @patch('repository.base_repository.Db_session')
    def test_get_role_ports(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        role_id = uuid4()
        port_id = uuid4()
        mock_port = SimpleNamespace(
            id=port_id,
            role_id=role_id,
            parent_id=None,
            name="input",
            direction="input",
            description="Input port",
            ttx=None,
            created_ts=None,
            updated_ts=None,
        )
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_port]

        repo = RoleRepository()
        result = repo.get_role_ports(mock_db, role_id)

        assert result == [
            {
                "id": str(port_id),
                "role_id": str(role_id),
                "parent_id": None,
                "name": "input",
                "direction": "input",
                "description": "Input port",
                "ttx": None,
                "created_ts": None,
                "updated_ts": None,
            }
        ]

    @patch('repository.base_repository.Db_session')
    def test_create_role_port_success(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        role_id = uuid4()
        role = SimpleNamespace(id=role_id)

        def query_side_effect(model):
            query = MagicMock()
            if model is ModuleRole:
                query.filter.return_value.first.return_value = role
                return query
            if model is RolePort:
                query.filter.return_value.first.return_value = None
                return query
            raise AssertionError(f"Unexpected model {model}")

        mock_db.query.side_effect = query_side_effect
        repo = RoleRepository()
        result = repo.create_role_port(role_id, "input", "input", "Input", None)

        assert result["name"] == "input"
        assert result["direction"] == "input"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_normalize_port_direction_rejects_unknown_value(self):
        repo = RoleRepository()

        with pytest.raises(ValueError, match="Неверное направление"):
            repo._normalize_port_direction("sideways")

    @patch('repository.base_repository.Db_session')
    def test_update_role_success(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        role_id = uuid4()
        mock_role = MagicMock()
        mock_role.id = role_id
        mock_role.name = "old"
        mock_role.description = "Old"
        mock_role.created_ts = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_role

        repo = RoleRepository()
        result = repo.update_role(role_id, "new", "New")

        assert result["name"] == "new"
        assert result["description"] == "New"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_role)

    @patch('repository.base_repository.Db_session')
    def test_update_role_not_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        repo = RoleRepository()
        result = repo.update_role(uuid4(), "new", None)

        assert result is None
        mock_db.commit.assert_not_called()

    @patch('repository.base_repository.Db_session')
    def test_delete_role_success(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        role_id = uuid4()
        mock_role = MagicMock()
        mock_role.id = role_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_role

        repo = RoleRepository()
        result = repo.delete_role(role_id)

        assert result is True
        assert mock_db.execute.call_count == 4
        mock_db.delete.assert_called_once_with(mock_role)
        mock_db.commit.assert_called_once()

    @patch('repository.base_repository.Db_session')
    def test_delete_role_not_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        repo = RoleRepository()
        result = repo.delete_role(uuid4())

        assert result is False
        mock_db.execute.assert_not_called()
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
