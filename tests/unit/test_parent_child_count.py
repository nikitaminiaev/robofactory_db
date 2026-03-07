"""
Тест счётчика дублирующихся связей parent_child_module.

Когда один и тот же дочерний модуль добавляется к родителю повторно,
вместо ошибки UniqueViolation должен инкрементироваться счётчик count.

Логика реализована через PostgreSQL INSERT ... ON CONFLICT DO UPDATE.
Тесты проверяют:
  - что SQL-выражение содержит ON CONFLICT (уpsert вместо plain insert);
  - что маршрут PATCH не падает при повторном добавлении того же ребёнка.
"""
import pytest
from uuid import UUID
from unittest.mock import MagicMock, patch, call
from fastapi import FastAPI
from fastapi.testclient import TestClient

from repository.module_repository import ModuleRepository
from repository.role_repository import RoleRepository
from routes.create_basic_object import router


PARENT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
CHILD_ID  = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


# ---------------------------------------------------------------------------
# Вспомогательные фикстуры
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    application = FastAPI()
    application.include_router(router)
    return application


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


def _make_module_mock(module_id: UUID = PARENT_ID) -> MagicMock:
    mock = MagicMock()
    mock.id = module_id
    mock.bounding_contour = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# Тесты на уровне репозитория
# ---------------------------------------------------------------------------

class TestAddChildRelationUpsert:
    """Проверяет, что add_child_relation использует ON CONFLICT DO UPDATE."""

    @patch("repository.base_repository.Db_session")
    def test_upsert_statement_contains_on_conflict(self, mock_db_session_class):
        """SQL-выражение, переданное в db.execute, должно содержать ON CONFLICT."""
        mock_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_session_instance

        mock_db = MagicMock()
        captured_stmts: list = []

        def capture_execute(stmt):
            captured_stmts.append(stmt)

        mock_db.execute.side_effect = capture_execute

        repo = ModuleRepository()
        repo.add_child_relation(
            parent_id=PARENT_ID,
            child_id=CHILD_ID,
            coordinates={"x": 0, "y": 0, "z": 0, "rx": 0, "ry": 0, "rz": 0},
            db_session=mock_db,
        )

        assert len(captured_stmts) == 1, "execute должен быть вызван ровно один раз"
        stmt = captured_stmts[0]

        # Компилируем под PostgreSQL и проверяем наличие ON CONFLICT
        from sqlalchemy.dialects import postgresql
        compiled = stmt.compile(dialect=postgresql.dialect())
        sql_text = str(compiled)

        assert "ON CONFLICT" in sql_text.upper(), (
            f"Ожидался ON CONFLICT в SQL, получено:\n{sql_text}"
        )
        assert "DO UPDATE" in sql_text.upper(), (
            f"Ожидался DO UPDATE в SQL, получено:\n{sql_text}"
        )

    @patch("repository.base_repository.Db_session")
    def test_add_parent_relation_upsert_statement(self, mock_db_session_class):
        """add_parent_relation тоже должен использовать ON CONFLICT DO UPDATE."""
        mock_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_session_instance

        mock_db = MagicMock()
        captured_stmts: list = []

        mock_db.execute.side_effect = lambda stmt: captured_stmts.append(stmt)

        repo = ModuleRepository()
        repo.add_parent_relation(
            child_id=CHILD_ID,
            parent_id=PARENT_ID,
            db_session=mock_db,
        )

        assert len(captured_stmts) == 1
        stmt = captured_stmts[0]

        from sqlalchemy.dialects import postgresql
        compiled = stmt.compile(dialect=postgresql.dialect())
        sql_text = str(compiled)

        assert "ON CONFLICT" in sql_text.upper()
        assert "DO UPDATE" in sql_text.upper()


# ---------------------------------------------------------------------------
# Тесты на уровне маршрута PATCH /api/basic_object/{id}
# ---------------------------------------------------------------------------

class TestDuplicateChildViaRoute:
    """
    Проверяет поведение маршрута при добавлении одного и того же дочернего
    модуля дважды подряд — ошибки быть не должно.
    """

    def test_same_child_added_twice_no_error(self, app, client):
        """
        При двух последовательных PATCH-запросах с одинаковым child_id
        оба запроса должны вернуть 200, а add_child_relation — быть вызван дважды.
        """
        module_mock = _make_module_mock()
        repo_mock = MagicMock()
        repo_mock.get_module_for_update.return_value = module_mock
        repo_mock.add_child_relation.return_value = None

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository] = lambda: MagicMock()

        payload = {
            "added_children": [
                {
                    "id": str(CHILD_ID),
                    "coordinates": {"x": 0, "y": 0, "z": 0, "rx": 0, "ry": 0, "rz": 0},
                }
            ]
        }

        try:
            response_1 = client.patch(f"/api/basic_object/{PARENT_ID}", json=payload)
            response_2 = client.patch(f"/api/basic_object/{PARENT_ID}", json=payload)
        finally:
            app.dependency_overrides.clear()

        assert response_1.status_code == 200, f"Первый запрос: {response_1.text}"
        assert response_2.status_code == 200, f"Второй запрос: {response_2.text}"
        assert response_1.json()["ok"] is True
        assert response_2.json()["ok"] is True
        assert repo_mock.add_child_relation.call_count == 2

    def test_same_child_added_twice_calls_with_correct_ids(self, app, client):
        """
        При дублировании add_child_relation оба вызова должны получать
        одинаковые parent_id и child_id.
        """
        module_mock = _make_module_mock()
        repo_mock = MagicMock()
        repo_mock.get_module_for_update.return_value = module_mock
        repo_mock.add_child_relation.return_value = None

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository] = lambda: MagicMock()

        payload = {
            "added_children": [{"id": str(CHILD_ID)}]
        }

        try:
            client.patch(f"/api/basic_object/{PARENT_ID}", json=payload)
            client.patch(f"/api/basic_object/{PARENT_ID}", json=payload)
        finally:
            app.dependency_overrides.clear()

        assert repo_mock.add_child_relation.call_count == 2

        for single_call in repo_mock.add_child_relation.call_args_list:
            assert single_call.kwargs["parent_id"] == PARENT_ID
            assert single_call.kwargs["child_id"] == CHILD_ID
