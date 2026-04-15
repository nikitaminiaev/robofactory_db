"""
Тесты для parent_child_module с суррогатным UUID PK.

Новая схема позволяет иметь несколько записей с одной парой (parent_id, child_id)
при разных координатах. Поле count удалено; количество вхождений определяется
числом строк через GROUP BY.
"""
import pytest
import uuid
from uuid import UUID
from unittest.mock import MagicMock, patch, call
from sqlalchemy.dialects import postgresql
from fastapi import FastAPI
from fastapi.testclient import TestClient

from repository.module_repository import ModuleRepository
from repository.role_repository import RoleRepository
from routes.create_basic_object import router

PARENT_ID = UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')
CHILD_ID  = UUID('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')

COORDS_A = {'x': 0,  'y': 0,  'z': 0,  'rx': 0, 'ry': 0, 'rz': 0}
COORDS_B = {'x': 10, 'y': 20, 'z': 30, 'rx': 0, 'ry': 0, 'rz': 0}


# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def app():
    application = FastAPI()
    application.include_router(router)
    return application


@pytest.fixture(scope='module')
def client(app):
    return TestClient(app)


def _make_module_mock(module_id: UUID = PARENT_ID) -> MagicMock:
    mock = MagicMock()
    mock.id = module_id
    mock.bounding_contour = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# Тесты на уровне репозитория: add_child_relation / add_parent_relation
# ---------------------------------------------------------------------------

class TestAddChildRelationInsert:
    """Проверяет, что add_child_relation выполняет plain INSERT без ON CONFLICT."""

    @patch('repository.base_repository.Db_session')
    def test_each_call_executes_insert(self, mock_db_class):
        """Каждый вызов add_child_relation делает один INSERT."""
        mock_db_instance = MagicMock()
        mock_db_class.return_value = mock_db_instance
        mock_db = MagicMock()

        captured = []
        mock_db.execute.side_effect = lambda stmt: captured.append(stmt)

        repo = ModuleRepository()
        repo.add_child_relation(
            parent_id=PARENT_ID, child_id=CHILD_ID,
            coordinates=COORDS_A, db_session=mock_db,
        )
        repo.add_child_relation(
            parent_id=PARENT_ID, child_id=CHILD_ID,
            coordinates=COORDS_B, db_session=mock_db,
        )

        assert mock_db.execute.call_count == 2, 'ожидалось два вызова execute'

    @patch('repository.base_repository.Db_session')
    def test_no_on_conflict_in_sql(self, mock_db_class):
        """SQL-выражение НЕ должно содержать ON CONFLICT."""
        mock_db_class.return_value = MagicMock()
        mock_db = MagicMock()
        captured = []
        mock_db.execute.side_effect = lambda stmt: captured.append(stmt)

        repo = ModuleRepository()
        repo.add_child_relation(
            parent_id=PARENT_ID, child_id=CHILD_ID,
            coordinates=COORDS_A, db_session=mock_db,
        )

        assert len(captured) == 1
        sql = str(captured[0].compile(dialect=postgresql.dialect())).upper()
        assert 'ON CONFLICT' not in sql, f'SQL не должен содержать ON CONFLICT: {sql}'
        assert 'INSERT' in sql

    @patch('repository.base_repository.Db_session')
    def test_two_calls_generate_different_ids(self, mock_db_class):
        """Два вызова add_child_relation генерируют два разных UUID."""
        mock_db_class.return_value = MagicMock()
        mock_db = MagicMock()
        captured_params = []

        def capture(stmt):
            compiled = stmt.compile(dialect=postgresql.dialect(), compile_kwargs={'literal_binds': False})
            captured_params.append(dict(compiled.params))

        mock_db.execute.side_effect = capture

        repo = ModuleRepository()
        repo.add_child_relation(PARENT_ID, CHILD_ID, COORDS_A, db_session=mock_db)
        repo.add_child_relation(PARENT_ID, CHILD_ID, COORDS_B, db_session=mock_db)

        ids = [p['id'] for p in captured_params]
        assert ids[0] != ids[1], 'два вызова должны генерировать разные UUID'

    @patch('repository.base_repository.Db_session')
    def test_different_coordinates_create_separate_rows(self, mock_db_class):
        """Разные координаты для одной пары (parent, child) → отдельные строки."""
        mock_db_class.return_value = MagicMock()
        mock_db = MagicMock()
        captured_params = []

        def capture(stmt):
            compiled = stmt.compile(dialect=postgresql.dialect(), compile_kwargs={'literal_binds': False})
            captured_params.append(dict(compiled.params))

        mock_db.execute.side_effect = capture

        repo = ModuleRepository()
        repo.add_child_relation(PARENT_ID, CHILD_ID, COORDS_A, db_session=mock_db)
        repo.add_child_relation(PARENT_ID, CHILD_ID, COORDS_B, db_session=mock_db)

        assert mock_db.execute.call_count == 2
        # Убеждаемся, что оба parent_id/child_id одинаковые, но id — разные
        assert captured_params[0]['parent_id'] == captured_params[1]['parent_id']
        assert captured_params[0]['child_id']  == captured_params[1]['child_id']
        assert captured_params[0]['id'] != captured_params[1]['id']

    @patch('repository.base_repository.Db_session')
    def test_add_parent_relation_plain_insert(self, mock_db_class):
        """add_parent_relation тоже использует plain INSERT без ON CONFLICT."""
        mock_db_class.return_value = MagicMock()
        mock_db = MagicMock()
        captured = []
        mock_db.execute.side_effect = lambda stmt: captured.append(stmt)

        repo = ModuleRepository()
        repo.add_parent_relation(CHILD_ID, PARENT_ID, COORDS_A, db_session=mock_db)

        assert len(captured) == 1
        sql = str(captured[0].compile(dialect=postgresql.dialect())).upper()
        assert 'ON CONFLICT' not in sql
        assert 'INSERT' in sql


# ---------------------------------------------------------------------------
# Тесты на get_child_counts
# ---------------------------------------------------------------------------

class TestGetChildCounts:
    """get_child_counts считает строки через GROUP BY, не читает поле count."""

    @patch('repository.base_repository.Db_session')
    def test_counts_grouped_by_child_id(self, mock_db_class):
        """Три строки с двумя уникальными child_id → правильный словарь."""
        mock_db_instance = MagicMock()
        mock_db_class.return_value = mock_db_instance

        child_a = UUID('cccccccc-cccc-cccc-cccc-cccccccccccc')
        child_b = UUID('dddddddd-dddd-dddd-dddd-dddddddddddd')

        # Имитируем результат GROUP BY: child_a встречается 2 раза, child_b — 1
        row_a = MagicMock()
        row_a.child_id = child_a
        row_a.cnt = 2
        row_b = MagicMock()
        row_b.child_id = child_b
        row_b.cnt = 1

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [row_a, row_b]
        mock_db_instance.session.return_value.__enter__.return_value = mock_db

        repo = ModuleRepository()
        result = repo.get_child_counts(PARENT_ID)

        assert result == {str(child_a): 2, str(child_b): 1}

    @patch('repository.base_repository.Db_session')
    def test_empty_result_returns_empty_dict(self, mock_db_class):
        """При отсутствии дочерних модулей возвращается пустой словарь."""
        mock_db_instance = MagicMock()
        mock_db_class.return_value = mock_db_instance

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = []
        mock_db_instance.session.return_value.__enter__.return_value = mock_db

        repo = ModuleRepository()
        result = repo.get_child_counts(PARENT_ID)

        assert result == {}


# ---------------------------------------------------------------------------
# Тесты на copy_module_with_roles (INSERT с id=uuid4())
# ---------------------------------------------------------------------------

class TestCopyModuleRelations:
    """copy_module_with_roles копирует все строки parent_child_module с новыми UUID."""

    @patch('repository.base_repository.Db_session')
    def test_copy_inserts_child_relations_with_new_ids(self, mock_db_class):
        """
        При копировании модуля-ребёнка все строки, где оригинал — child,
        вставляются заново с новым child_id=new_module.id и новым id.
        """
        mock_db_instance = MagicMock()
        mock_db_class.return_value = mock_db_instance

        original_id = UUID('11111111-1111-1111-1111-111111111111')
        new_id      = UUID('22222222-2222-2222-2222-222222222222')

        # Строки где оригинал — child
        rel = MagicMock()
        rel.parent_id   = PARENT_ID
        rel.child_id    = original_id
        rel.coordinates = COORDS_A
        rel.role_id     = None

        original_module = MagicMock()
        original_module.id = original_id
        original_module.bounding_contour = None

        new_module = MagicMock()
        new_module.id = new_id

        mock_db = MagicMock()
        mock_db.query.return_value.options.return_value.filter_by.return_value.first.return_value = original_module
        mock_db.flush.return_value = None

        # Первый query(parent_child_module).filter → child_relations = [rel]
        # Второй query(parent_child_module).filter → parent_relations = []
        # Третий query(Module)... → new_module (финальный SELECT)
        child_filter = MagicMock()
        child_filter.all.return_value = [rel]
        parent_filter = MagicMock()
        parent_filter.all.return_value = []

        call_counter = {'n': 0}
        def mock_query(arg):
            from models.associations import parent_child_module as pcm
            from models import Module
            if arg is pcm:
                call_counter['n'] += 1
                mock_f = MagicMock()
                if call_counter['n'] == 1:
                    mock_f.filter.return_value = child_filter
                else:
                    mock_f.filter.return_value = parent_filter
                return mock_f
            else:
                # Module query
                q = MagicMock()
                q.options.return_value.filter_by.return_value.first.return_value = new_module
                return q

        mock_db.query.side_effect = mock_query

        # Перехватываем INSERT-вызовы
        inserted_params = []
        def capture_execute(stmt):
            try:
                compiled = stmt.compile(
                    dialect=postgresql.dialect(),
                    compile_kwargs={'literal_binds': False},
                )
                inserted_params.append(dict(compiled.params))
            except Exception:
                pass

        mock_db.execute.side_effect = capture_execute
        mock_db_instance.session.return_value.__enter__.return_value = mock_db

        from repository.module_repository import ModuleRepository as Repo
        repo = Repo()
        result = repo.copy_module_with_roles(
            module_id=original_id,
            new_author='tester',
            version_number='2.0',
            description='copy',
        )

        # Должен быть хотя бы один INSERT
        assert mock_db.execute.call_count >= 1
        # Каждая вставленная строка должна иметь поле id
        for params in inserted_params:
            assert 'id' in params, f'INSERT должен содержать поле id: {params}'


# ---------------------------------------------------------------------------
# Маршрутные тесты: PATCH — два добавления одного ребёнка
# ---------------------------------------------------------------------------

class TestDuplicateChildViaRoute:
    """Повторное добавление того же дочернего модуля не даёт ошибки."""

    def test_same_child_added_twice_returns_200_both_times(self, app, client):
        module_mock = _make_module_mock()
        repo_mock = MagicMock()
        repo_mock.get_module_for_update.return_value = module_mock
        repo_mock.add_child_relation.return_value = None

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository]   = lambda: MagicMock()

        payload = {'added_children': [{'id': str(CHILD_ID), 'coordinates': COORDS_A}]}

        try:
            r1 = client.patch(f'/api/basic_object/{PARENT_ID}', json=payload)
            r2 = client.patch(f'/api/basic_object/{PARENT_ID}', json=payload)
        finally:
            app.dependency_overrides.clear()

        assert r1.status_code == 200, r1.text
        assert r2.status_code == 200, r2.text
        assert repo_mock.add_child_relation.call_count == 2

    def test_same_child_twice_add_child_relation_called_with_correct_ids(self, app, client):
        module_mock = _make_module_mock()
        repo_mock = MagicMock()
        repo_mock.get_module_for_update.return_value = module_mock
        repo_mock.add_child_relation.return_value = None

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository]   = lambda: MagicMock()

        payload = {'added_children': [{'id': str(CHILD_ID)}]}

        try:
            client.patch(f'/api/basic_object/{PARENT_ID}', json=payload)
            client.patch(f'/api/basic_object/{PARENT_ID}', json=payload)
        finally:
            app.dependency_overrides.clear()

        assert repo_mock.add_child_relation.call_count == 2
        for c in repo_mock.add_child_relation.call_args_list:
            assert c.kwargs['parent_id'] == PARENT_ID
            assert c.kwargs['child_id']  == CHILD_ID

    def test_add_child_with_different_coordinates_both_succeed(self, app, client):
        """Добавление одного ребёнка с разными координатами — оба запроса успешны."""
        module_mock = _make_module_mock()
        repo_mock = MagicMock()
        repo_mock.get_module_for_update.return_value = module_mock
        repo_mock.add_child_relation.return_value = None

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository]   = lambda: MagicMock()

        try:
            r1 = client.patch(f'/api/basic_object/{PARENT_ID}',
                              json={'added_children': [{'id': str(CHILD_ID), 'coordinates': COORDS_A}]})
            r2 = client.patch(f'/api/basic_object/{PARENT_ID}',
                              json={'added_children': [{'id': str(CHILD_ID), 'coordinates': COORDS_B}]})
        finally:
            app.dependency_overrides.clear()

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert repo_mock.add_child_relation.call_count == 2
        calls_coords = [c.kwargs.get('coordinates') for c in repo_mock.add_child_relation.call_args_list]
        assert calls_coords[0] != calls_coords[1], 'координаты должны различаться'
