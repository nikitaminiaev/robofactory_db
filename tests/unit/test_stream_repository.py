from types import SimpleNamespace
from uuid import UUID
from unittest.mock import MagicMock, patch

import pytest

from models import Module, RolePort, Stream
from repository.stream_repository import StreamRepository


class TestStreamRepository:
    @patch('repository.base_repository.Db_session')
    def test_get_module_role_streams_returns_only_requested_module_streams(self, mock_db_session_class):
        module_id = UUID('11111111-1111-1111-1111-111111111111')
        source_role_id = UUID('22222222-2222-2222-2222-222222222222')
        target_role_id = UUID('33333333-3333-3333-3333-333333333333')
        stream_id = UUID('44444444-4444-4444-4444-444444444444')

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            SimpleNamespace(
                source_role_id=source_role_id,
                target_role_id=target_role_id,
                source_port_id=None,
                source_port_name=None,
                target_port_id=None,
                target_port_name=None,
                id=stream_id,
                name='power',
                description='Power stream',
            )
        ]

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = StreamRepository()
        result = repo.get_module_role_streams(module_id)

        assert result == [
            {
                'id': str(stream_id),
                'name': 'power',
                'description': 'Power stream',
                'source_role_id': str(source_role_id),
                'target_role_id': str(target_role_id),
                'source_port_id': None,
                'source_port_name': None,
                'target_port_id': None,
                'target_port_name': None,
            }
        ]
        sql = str(mock_db.execute.call_args.args[0])
        assert 'module_role_stream.module_id = :module_id_1' in sql

    @patch('repository.base_repository.Db_session')
    def test_get_external_role_streams_returns_parent_streams_involving_external_role(self, mock_db_session_class):
        child_id = UUID('11111111-1111-1111-1111-111111111111')
        parent_id = UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')
        external_role_id = UUID('22222222-2222-2222-2222-222222222222')
        internal_parent_role_id = UUID('33333333-3333-3333-3333-333333333333')
        stream_id = UUID('44444444-4444-4444-4444-444444444444')

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            SimpleNamespace(
                parent_module_id=parent_id,
                external_role_id=external_role_id,
                parent_module_name='Parent module',
                source_role_id=external_role_id,
                source_role_name='External input',
                target_role_id=internal_parent_role_id,
                target_role_name='Controller',
                source_port_id=None,
                source_port_name=None,
                target_port_id=None,
                target_port_name=None,
                id=stream_id,
                name='commands',
                description='Command stream',
                external_role_name='External input',
            )
        ]

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = StreamRepository()
        result = repo.get_external_role_streams(child_id)

        assert result == [
            {
                'id': str(stream_id),
                'name': 'commands',
                'description': 'Command stream',
                'parent_module_id': str(parent_id),
                'parent_module_name': 'Parent module',
                'source_role_id': str(external_role_id),
                'source_role_name': 'External input',
                'target_role_id': str(internal_parent_role_id),
                'target_role_name': 'Controller',
                'source_port_id': None,
                'source_port_name': None,
                'target_port_id': None,
                'target_port_name': None,
                'external_roles': [
                    {'id': str(external_role_id), 'name': 'External input'},
                ],
            }
        ]

        sql = str(mock_db.execute.call_args.args[0])
        assert 'parent_child_module.child_id = :child_id_1' in sql
        assert 'module_role_stream.module_id = anon_1.parent_module_id' in sql
        assert 'module_role_stream.source_role_id = anon_1.external_role_id' in sql
        assert 'module_role_stream.target_role_id = anon_1.external_role_id' in sql

    @patch('repository.base_repository.Db_session')
    def test_get_external_role_streams_deduplicates_streams_between_external_roles(self, mock_db_session_class):
        child_id = UUID('11111111-1111-1111-1111-111111111111')
        parent_id = UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')
        source_role_id = UUID('22222222-2222-2222-2222-222222222222')
        target_role_id = UUID('33333333-3333-3333-3333-333333333333')
        stream_id = UUID('44444444-4444-4444-4444-444444444444')

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            SimpleNamespace(
                parent_module_id=parent_id,
                external_role_id=source_role_id,
                parent_module_name='Parent module',
                source_role_id=source_role_id,
                source_role_name='Source role',
                target_role_id=target_role_id,
                target_role_name='Target role',
                source_port_id=None,
                source_port_name=None,
                target_port_id=None,
                target_port_name=None,
                id=stream_id,
                name='shared',
                description=None,
                external_role_name='Source role',
            ),
            SimpleNamespace(
                parent_module_id=parent_id,
                external_role_id=target_role_id,
                parent_module_name='Parent module',
                source_role_id=source_role_id,
                source_role_name='Source role',
                target_role_id=target_role_id,
                target_role_name='Target role',
                source_port_id=None,
                source_port_name=None,
                target_port_id=None,
                target_port_name=None,
                id=stream_id,
                name='shared',
                description=None,
                external_role_name='Target role',
            ),
        ]

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = StreamRepository()
        result = repo.get_external_role_streams(child_id)

        assert len(result) == 1
        assert result[0]['external_roles'] == [
            {'id': str(source_role_id), 'name': 'Source role'},
            {'id': str(target_role_id), 'name': 'Target role'},
        ]

    @patch('repository.base_repository.Db_session')
    def test_upsert_module_role_stream_allows_empty_ports(self, mock_db_session_class):
        module_id = UUID('11111111-1111-1111-1111-111111111111')
        source_role_id = UUID('22222222-2222-2222-2222-222222222222')
        target_role_id = UUID('33333333-3333-3333-3333-333333333333')
        stream_id = UUID('44444444-4444-4444-4444-444444444444')

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            SimpleNamespace(role_id=source_role_id),
            SimpleNamespace(role_id=target_role_id),
        ]
        mock_db.execute.return_value.first.return_value = None

        def query_side_effect(model):
            query = MagicMock()
            if model is Module:
                query.filter.return_value.first.return_value = SimpleNamespace(id=module_id)
                return query
            if model is Stream:
                query.filter.return_value.first.return_value = SimpleNamespace(
                    id=stream_id,
                    name='power',
                    description='Power stream',
                )
                return query
            raise AssertionError(f'Unexpected model {model}')

        mock_db.query.side_effect = query_side_effect
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db
        mock_db_session_class.return_value = mock_db_session_instance

        repo = StreamRepository()
        result = repo.upsert_module_role_stream(
            module_id,
            source_role_id,
            target_role_id,
            'power',
            None,
        )

        assert result['source_port_id'] is None
        assert result['target_port_id'] is None
        mock_db.commit.assert_called_once()

    def test_ensure_port_belongs_to_role_rejects_foreign_port(self):
        repo = StreamRepository()
        role_id = UUID('22222222-2222-2222-2222-222222222222')
        port_id = UUID('55555555-5555-5555-5555-555555555555')
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(
            id=port_id,
            role_id=UUID('33333333-3333-3333-3333-333333333333'),
        )

        with pytest.raises(ValueError, match='не принадлежит'):
            repo._ensure_port_belongs_to_role(mock_db, port_id, role_id, 'source_port_id')
