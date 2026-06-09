from types import SimpleNamespace
from uuid import UUID
from unittest.mock import MagicMock, patch

import pytest

from models import Module
from models.interface_object import InterfaceObject
from models.interface_mapping import InterfaceMapping
from repository.interface_repository import InterfaceRepository, InterfaceMappingRepository


class TestInterfaceRepository:
    @patch('repository.base_repository.Db_session')
    def test_get_module_interfaces_returns_interfaces_for_module(self, mock_db_session_class):
        module_id = UUID('11111111-1111-1111-1111-111111111111')
        iface_id = UUID('22222222-2222-2222-2222-222222222222')

        mock_iface = MagicMock(spec=InterfaceObject)
        mock_iface.id = iface_id
        mock_iface.name = "power connector"
        mock_iface.direction = "input"
        mock_iface.physical_form = "terminal 2-pin"
        mock_iface.parameters = {"voltage": 24, "current_max": 15}
        mock_iface.is_mandatory = True
        mock_iface.is_service = False
        mock_iface.module_id = module_id
        mock_iface.description = "Test"
        mock_iface.ttx = None
        mock_iface.coordinates = None
        mock_iface.created_ts = None
        mock_iface.updated_ts = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_iface]

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceRepository()
        result = repo.get_module_interfaces(module_id)

        assert len(result) == 1
        assert result[0]["name"] == "power connector"
        assert result[0]["direction"] == "input"
        assert result[0]["physical_form"] == "terminal 2-pin"
        assert result[0]["parameters"] == {"voltage": 24, "current_max": 15}
        assert result[0]["is_mandatory"] is True
        assert result[0]["is_service"] is False

    @patch('repository.base_repository.Db_session')
    def test_create_interface_creates_with_correct_fields(self, mock_db_session_class):
        module_id = UUID('11111111-1111-1111-1111-111111111111')
        iface_id = UUID('22222222-2222-2222-2222-222222222222')

        mock_module = MagicMock(spec=Module)
        mock_module.id = module_id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_module

        def add_side_effect(obj):
            obj.id = iface_id
        mock_db.add.side_effect = add_side_effect
        mock_db.commit.return_value = None

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceRepository()
        result = repo.create_interface(
            module_id=module_id,
            name="CAN bus",
            direction="bidirectional",
            physical_form="M12 D-coded",
            parameters={"protocol": "CANopen", "baudrate": 1000000},
            is_mandatory=True,
            is_service=False,
            description="CAN bus interface",
        )

        mock_db.add.assert_called_once()
        added = mock_db.add.call_args[0][0]
        assert isinstance(added, InterfaceObject)
        assert added.name == "CAN bus"
        assert added.direction == "bidirectional"
        assert added.physical_form == "M12 D-coded"
        assert added.parameters == {"protocol": "CANopen", "baudrate": 1000000}

    @patch('repository.base_repository.Db_session')
    def test_update_interface_updates_partial_fields(self, mock_db_session_class):
        iface_id = UUID('22222222-2222-2222-2222-222222222222')

        mock_iface = MagicMock(spec=InterfaceObject)
        mock_iface.id = iface_id
        mock_iface.name = "old name"
        mock_iface.module_id = UUID('11111111-1111-1111-1111-111111111111')
        mock_iface.direction = "input"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_iface

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceRepository()
        result = repo.update_interface(
            interface_id=iface_id,
            name="new name",
            direction="output",
        )

        assert mock_iface.name == "new name"
        assert mock_iface.direction == "output"

    @patch('repository.base_repository.Db_session')
    def test_delete_interface_removes_it(self, mock_db_session_class):
        iface_id = UUID('22222222-2222-2222-2222-222222222222')

        mock_iface = MagicMock(spec=InterfaceObject)
        mock_iface.id = iface_id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_iface

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceRepository()
        result = repo.delete_interface(iface_id)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_iface)

    @patch('repository.base_repository.Db_session')
    def test_delete_interface_not_found(self, mock_db_session_class):
        iface_id = UUID('22222222-2222-2222-2222-222222222222')

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceRepository()
        result = repo.delete_interface(iface_id)

        assert result is False
        mock_db.delete.assert_not_called()

    @patch('repository.base_repository.Db_session')
    def test_create_interface_raises_on_missing_module(self, mock_db_session_class):
        module_id = UUID('11111111-1111-1111-1111-111111111111')

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceRepository()
        with pytest.raises(ValueError, match="Module with ID"):
            repo.create_interface(module_id=module_id, name="test")

class TestInterfaceMappingRepository:
    @patch('repository.base_repository.Db_session')
    def test_create_mapping_creates_with_correct_data(self, mock_db_session_class):
        module_id = UUID('11111111-1111-1111-1111-111111111111')
        role_port_id = UUID('33333333-3333-3333-3333-333333333333')
        interface_id = UUID('22222222-2222-2222-2222-222222222222')
        mapping_id = UUID('44444444-4444-4444-4444-444444444444')

        mock_module = MagicMock(spec=Module)
        mock_module.id = module_id

        mock_role = MagicMock()
        mock_role.id = UUID('55555555-5555-5555-5555-555555555555')
        mock_role.name = "main role"
        mock_module.roles = [mock_role]

        mock_port = MagicMock()
        mock_port.id = role_port_id
        mock_port.name = "power port"
        mock_port.role_id = mock_role.id

        mock_iface = MagicMock(spec=InterfaceObject)
        mock_iface.id = interface_id
        mock_iface.module_id = module_id

        mock_iface_enrich = MagicMock(spec=InterfaceObject)
        mock_iface_enrich.id = interface_id
        mock_iface_enrich.name = "test interface"

        mock_db = MagicMock()
        mock_db.execute.return_value.first.return_value = SimpleNamespace(role_id=mock_role.id)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_module,   # 1. check module exists
            mock_port,     # 2. check port exists
            mock_iface,    # 3. check interface exists
            None,          # 4. no existing mapping
            mock_iface_enrich,  # 5. _enrich: interface
            mock_port,     # 6. _enrich: port
            mock_role,     # 7. _enrich: role
        ]

        def add_side_effect(obj):
            obj.id = mapping_id
        mock_db.add.side_effect = add_side_effect

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceMappingRepository()
        result = repo.create_mapping(module_id, role_port_id, interface_id)

        mock_db.add.assert_called_once()
        added = mock_db.add.call_args[0][0]
        assert isinstance(added, InterfaceMapping)
        assert added.module_id == module_id
        assert added.role_port_id == role_port_id
        assert added.interface_id == interface_id

    @patch('repository.base_repository.Db_session')
    def test_create_mapping_raises_on_missing_module(self, mock_db_session_class):
        module_id = UUID('11111111-1111-1111-1111-111111111111')
        role_port_id = UUID('33333333-3333-3333-3333-333333333333')
        interface_id = UUID('22222222-2222-2222-2222-222222222222')

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [None]  # module not found

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceMappingRepository()
        with pytest.raises(ValueError, match="Module with ID"):
            repo.create_mapping(module_id, role_port_id, interface_id)

    @patch('repository.base_repository.Db_session')
    def test_create_mapping_raises_when_port_role_is_not_external_for_module(self, mock_db_session_class):
        module_id = UUID('11111111-1111-1111-1111-111111111111')
        role_port_id = UUID('33333333-3333-3333-3333-333333333333')
        interface_id = UUID('22222222-2222-2222-2222-222222222222')

        mock_module = MagicMock(spec=Module)
        mock_module.id = module_id
        mock_module.roles = []

        mock_port = MagicMock()
        mock_port.id = role_port_id
        mock_port.role_id = UUID('55555555-5555-5555-5555-555555555555')

        mock_db = MagicMock()
        mock_db.execute.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_module,
            mock_port,
        ]

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceMappingRepository()
        with pytest.raises(ValueError, match="Порт не принадлежит внешней роли"):
            repo.create_mapping(module_id, role_port_id, interface_id)

    @patch('repository.base_repository.Db_session')
    def test_create_mapping_raises_when_interface_belongs_to_other_module(self, mock_db_session_class):
        module_id = UUID('11111111-1111-1111-1111-111111111111')
        other_module_id = UUID('99999999-9999-9999-9999-999999999999')
        role_port_id = UUID('33333333-3333-3333-3333-333333333333')
        interface_id = UUID('22222222-2222-2222-2222-222222222222')

        mock_role = MagicMock()
        mock_role.id = UUID('55555555-5555-5555-5555-555555555555')

        mock_module = MagicMock(spec=Module)
        mock_module.id = module_id
        mock_module.roles = [mock_role]

        mock_port = MagicMock()
        mock_port.id = role_port_id
        mock_port.role_id = mock_role.id

        mock_iface = MagicMock(spec=InterfaceObject)
        mock_iface.id = interface_id
        mock_iface.module_id = other_module_id

        mock_db = MagicMock()
        mock_db.execute.return_value.first.return_value = SimpleNamespace(role_id=mock_role.id)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_module,
            mock_port,
            mock_iface,
        ]

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceMappingRepository()
        with pytest.raises(ValueError, match="Интерфейс не принадлежит"):
            repo.create_mapping(module_id, role_port_id, interface_id)

    @patch('repository.base_repository.Db_session')
    def test_delete_mapping_removes_it(self, mock_db_session_class):
        mapping_id = UUID('44444444-4444-4444-4444-444444444444')

        mock_mapping = MagicMock(spec=InterfaceMapping)
        mock_mapping.id = mapping_id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_mapping

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceMappingRepository()
        result = repo.delete_mapping(mapping_id)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_mapping)

    @patch('repository.base_repository.Db_session')
    def test_delete_mapping_not_found(self, mock_db_session_class):
        mapping_id = UUID('44444444-4444-4444-4444-444444444444')

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceMappingRepository()
        result = repo.delete_mapping(mapping_id)

        assert result is False
        mock_db.delete.assert_not_called()

    @patch('repository.base_repository.Db_session')
    def test_create_mapping_returns_existing_if_duplicate(self, mock_db_session_class):
        module_id = UUID('11111111-1111-1111-1111-111111111111')
        role_port_id = UUID('33333333-3333-3333-3333-333333333333')
        interface_id = UUID('22222222-2222-2222-2222-222222222222')
        mapping_id = UUID('44444444-4444-4444-4444-444444444444')

        mock_mapping = MagicMock(spec=InterfaceMapping)
        mock_mapping.id = mapping_id
        mock_mapping.module_id = module_id
        mock_mapping.role_port_id = role_port_id
        mock_mapping.interface_id = interface_id
        mock_mapping.created_ts = None

        mock_module = MagicMock(spec=Module)
        mock_module.id = module_id

        mock_role = MagicMock()
        mock_role.id = UUID('55555555-5555-5555-5555-555555555555')
        mock_role.name = "main role"
        mock_module.roles = [mock_role]

        mock_port = MagicMock()
        mock_port.id = role_port_id
        mock_port.name = "power port"
        mock_port.role_id = mock_role.id

        mock_iface = MagicMock(spec=InterfaceObject)
        mock_iface.id = interface_id
        mock_iface.module_id = module_id

        mock_iface_enrich = MagicMock(spec=InterfaceObject)
        mock_iface_enrich.id = interface_id
        mock_iface_enrich.name = "test interface"

        mock_db = MagicMock()
        mock_db.execute.return_value.first.return_value = SimpleNamespace(role_id=mock_role.id)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_module,      # 1. check module exists
            mock_port,        # 2. check port exists
            mock_iface,       # 3. check interface exists
            mock_mapping,     # 4. existing mapping found
            mock_iface_enrich,  # 5. _enrich: interface
            mock_port,        # 6. _enrich: port
            mock_role,        # 7. _enrich: role
        ]

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = InterfaceMappingRepository()
        result = repo.create_mapping(module_id, role_port_id, interface_id)

        assert result["id"] == str(mapping_id)
        assert mock_db.add.call_count == 0
