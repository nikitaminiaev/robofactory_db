import pytest
from uuid import UUID
from types import SimpleNamespace
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

    @patch('repository.base_repository.Db_session')
    def test_get_parent_edges_with_roles_uses_scoped_parent_child_assignments(self, mock_db_session_class):
        """
        External Roles должны показывать только роли, назначенные конкретной
        parent-child связи, а не пересечение глобальных ролей parent/child.
        """
        child_id = UUID('11111111-1111-1111-1111-111111111111')
        parent_a_id = UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')
        parent_b_id = UUID('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')
        relation_a_id = UUID('aaaaaaaa-0000-0000-0000-aaaaaaaaaaaa')
        relation_b_id = UUID('bbbbbbbb-0000-0000-0000-bbbbbbbbbbbb')

        test_role_id = UUID('22222222-2222-2222-2222-222222222222')

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            SimpleNamespace(
                id=relation_a_id,
                parent_id=parent_a_id,
                role_id=test_role_id,
                name='test',
                description='для теста',
            ),
            SimpleNamespace(
                id=relation_b_id,
                parent_id=parent_b_id,
                role_id=None,
                name=None,
                description=None,
            ),
        ]

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = ModuleRepository()
        result = repo.get_parent_edges_with_roles(child_id)

        assert result == [
            {
                'parent_child_module_id': str(relation_a_id),
                'parent_id': str(parent_a_id),
                'role_id': str(test_role_id),
                'role_name': 'test',
                'role_description': 'для теста',
            },
            {
                'parent_child_module_id': str(relation_b_id),
                'parent_id': str(parent_b_id),
                'role_id': None,
                'role_name': None,
                'role_description': None,
            },
        ]

    @patch('repository.base_repository.Db_session')
    def test_get_children_roles_is_scoped_to_parent_child_links(self, mock_db_session_class):
        """
        Роли в матрице children должны читаться с parent_child_module_role_assignment
        для конкретного parent, а не с глобальной связи Module ↔ Role.
        Иначе назначение роли child в одном parent протекает в другой parent.
        """
        parent_id = UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')
        child_id = UUID('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')
        motor_role_id = UUID('cccccccc-cccc-cccc-cccc-cccccccccccc')

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            SimpleNamespace(child_id=child_id, role_id=motor_role_id),
        ]

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = ModuleRepository()
        result = repo.get_children_roles(parent_id)

        assert result == {str(child_id): [str(motor_role_id)]}
        sql = str(mock_db.execute.call_args.args[0])
        assert 'parent_child_module_role_assignment' in sql
        assert 'JOIN module_role_assignment' not in sql