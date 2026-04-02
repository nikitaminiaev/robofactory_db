"""
Тесты для нового функционала:
1. remove_child_relations — удаление конкретных связей по parent_child_module_id
2. child_depths в load_freecad — передача глубины загрузки детей
3. removed_child_relations в PATCH — удаление конкретных связей через API
"""
import pytest
import json
from uuid import UUID
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.create_basic_object import router as basic_object_router
from routes.freecad.load_freecad import router as freecad_router
from repository.module_repository import ModuleRepository
from repository.role_repository import RoleRepository


PARENT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
CHILD_ID_1 = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
CHILD_ID_2 = "cccccccc-cccc-cccc-cccc-cccccccccccc"
PCM_ID_1 = "11111111-1111-1111-1111-111111111111"
PCM_ID_2 = "22222222-2222-2222-2222-222222222222"


# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    application = FastAPI()
    application.include_router(basic_object_router)
    application.include_router(freecad_router)
    return application


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


def _make_module_mock():
    mock = MagicMock()
    mock.id = UUID(PARENT_ID)
    mock.bounding_contour = MagicMock()
    return mock


def _make_repo_mock():
    mock_repo = MagicMock()
    mock_repo.get_module_for_update.return_value = _make_module_mock()
    mock_repo.add_child_relation.return_value = None
    mock_repo.remove_children.return_value = None
    mock_repo.remove_child_relations.return_value = None
    return mock_repo


# ===========================================================================
# Тесты для remove_child_relations (репозиторий)
# ===========================================================================

class TestRemoveChildRelations:
    """Тесты метода remove_child_relations в ModuleRepository."""

    @patch('repository.base_repository.Db_session')
    def test_remove_child_relations_calls_execute(self, mock_db_class):
        """remove_child_relations вызывает execute один раз."""
        mock_db = MagicMock()
        captured = []
        mock_db.execute.side_effect = lambda stmt: captured.append(stmt)

        repo = ModuleRepository()
        repo.remove_child_relations(
            parent_id=UUID(PARENT_ID),
            relation_ids=[UUID(PCM_ID_1), UUID(PCM_ID_2)],
            db_session=mock_db,
        )

        assert mock_db.execute.call_count == 1
        assert len(captured) == 1

    @patch('repository.base_repository.Db_session')
    def test_remove_child_relations_empty_list(self, mock_db_class):
        """При пустом списке execute не вызывается."""
        mock_db = MagicMock()

        repo = ModuleRepository()
        repo.remove_child_relations(
            parent_id=UUID(PARENT_ID),
            relation_ids=[],
            db_session=mock_db,
        )

        mock_db.execute.assert_not_called()

    @patch('repository.base_repository.Db_session')
    def test_remove_children_calls_execute(self, mock_db_class):
        """remove_children вызывает execute один раз."""
        mock_db = MagicMock()
        captured = []
        mock_db.execute.side_effect = lambda stmt: captured.append(stmt)

        repo = ModuleRepository()
        repo.remove_children(
            parent_id=UUID(PARENT_ID),
            child_ids=[UUID(CHILD_ID_1), UUID(CHILD_ID_2)],
            db_session=mock_db,
        )

        assert mock_db.execute.call_count == 1
        assert len(captured) == 1


# ===========================================================================
# Тесты для PATCH /api/basic_object/{id} с removed_child_relations
# ===========================================================================

class TestRemoveChildRelationsRoute:
    """Тесты маршрута PATCH для удаления конкретных связей."""

    def test_remove_child_relations_success(self, app, client):
        """Удаление конкретных связей по parent_child_module_id."""
        repo_mock = _make_repo_mock()

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository] = lambda: MagicMock()

        try:
            payload = {
                "removed_child_relations": [PCM_ID_1, PCM_ID_2],
            }
            response = client.patch(f"/api/basic_object/{PARENT_ID}", json=payload)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["ok"] is True

        repo_mock.remove_child_relations.assert_called_once()
        call_args = repo_mock.remove_child_relations.call_args
        # Проверяем позиционные аргументы
        assert call_args.args[0] == UUID(PARENT_ID)
        relation_ids = call_args.args[1]
        assert UUID(PCM_ID_1) in relation_ids
        assert UUID(PCM_ID_2) in relation_ids

    def test_remove_children_success(self, app, client):
        """Удаление всех вхождений по child_id."""
        repo_mock = _make_repo_mock()

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository] = lambda: MagicMock()

        try:
            payload = {
                "removed_children": [CHILD_ID_1, CHILD_ID_2],
            }
            response = client.patch(f"/api/basic_object/{PARENT_ID}", json=payload)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["ok"] is True

        repo_mock.remove_children.assert_called_once()
        call_args = repo_mock.remove_children.call_args
        # Проверяем позиционные аргументы
        assert call_args.args[0] == UUID(PARENT_ID)
        child_ids = call_args.args[1]
        assert UUID(CHILD_ID_1) in child_ids
        assert UUID(CHILD_ID_2) in child_ids

    def test_add_and_remove_combined(self, app, client):
        """Одновременное добавление и удаление детей."""
        repo_mock = _make_repo_mock()

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository] = lambda: MagicMock()

        try:
            payload = {
                "added_children": [
                    {"id": CHILD_ID_1, "coordinates": {"x": 0, "y": 0, "z": 0, "rx": 0, "ry": 0, "rz": 0}},
                ],
                "removed_children": [CHILD_ID_2],
                "removed_child_relations": [PCM_ID_1],
            }
            response = client.patch(f"/api/basic_object/{PARENT_ID}", json=payload)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["ok"] is True

        repo_mock.add_child_relation.assert_called_once()
        repo_mock.remove_children.assert_called_once()
        repo_mock.remove_child_relations.assert_called_once()


# ===========================================================================
# Тесты для load_freecad с child_depths
# ===========================================================================

class TestLoadFreeCadWithChildDepths:
    """Тесты эндпоинта load_freecad с параметром child_depths."""

    @patch('routes.freecad.load_freecad.part_loader')
    def test_load_freecad_with_child_depths(self, mock_part_loader, client):
        """Загрузка во FreeCAD с настройками глубины детей."""
        mock_part_loader.load_part_to_freecad.return_value = True

        payload = {
            "child_depths": [
                {"child_id": CHILD_ID_1, "parent_child_module_id": PCM_ID_1, "depth": 2},
                {"child_id": CHILD_ID_2, "parent_child_module_id": PCM_ID_2, "depth": 0},
            ]
        }
        response = client.post(f"/api/basic_object/{PARENT_ID}/load_freecad", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        mock_part_loader.load_part_to_freecad.assert_called_once_with(
            id=PARENT_ID,
            child_depths=[
                {"child_id": CHILD_ID_1, "parent_child_module_id": PCM_ID_1, "depth": 2},
                {"child_id": CHILD_ID_2, "parent_child_module_id": PCM_ID_2, "depth": 0},
            ]
        )

    @patch('routes.freecad.load_freecad.part_loader')
    def test_load_freecad_empty_child_depths(self, mock_part_loader, client):
        """Загрузка во FreeCAD без настроек глубины (пустой массив)."""
        mock_part_loader.load_part_to_freecad.return_value = True

        payload = {"child_depths": []}
        response = client.post(f"/api/basic_object/{PARENT_ID}/load_freecad", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        mock_part_loader.load_part_to_freecad.assert_called_once_with(
            id=PARENT_ID,
            child_depths=[]
        )

    @patch('routes.freecad.load_freecad.part_loader')
    def test_load_freecad_no_body(self, mock_part_loader, client):
        """Загрузка во FreeCAD без тела запроса."""
        mock_part_loader.load_part_to_freecad.return_value = True

        response = client.post(f"/api/basic_object/{PARENT_ID}/load_freecad", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        mock_part_loader.load_part_to_freecad.assert_called_once_with(
            id=PARENT_ID,
            child_depths=[]
        )


# ===========================================================================
# Тесты для function.py (формирование JSON команды)
# ===========================================================================

class TestFunctionLoadObjectInNewDoc:
    """Тесты функции load_object_in_new_doc в function.py."""

    def test_load_object_in_new_doc_with_child_depths(self):
        """Формирование команды с child_depths."""
        from service.freecad.function import load_object_in_new_doc

        child_depths = [
            {"child_id": CHILD_ID_1, "parent_child_module_id": PCM_ID_1, "depth": 2},
        ]
        result = load_object_in_new_doc(PARENT_ID, child_depths)

        data = json.loads(result.strip())
        assert data["function_call"] == "load_object_in_new_doc"
        assert data["arguments"]["obj_id"] == PARENT_ID
        assert data["arguments"]["child_depths"] == child_depths

    def test_load_object_in_new_doc_empty_child_depths(self):
        """Формирование команды с пустым child_depths."""
        from service.freecad.function import load_object_in_new_doc

        result = load_object_in_new_doc(PARENT_ID, [])

        data = json.loads(result.strip())
        assert data["function_call"] == "load_object_in_new_doc"
        assert data["arguments"]["obj_id"] == PARENT_ID
        assert data["arguments"]["child_depths"] == []

    def test_load_object_in_new_doc_none_child_depths(self):
        """Формирование команды с None child_depths."""
        from service.freecad.function import load_object_in_new_doc

        result = load_object_in_new_doc(PARENT_ID, None)

        data = json.loads(result.strip())
        assert data["function_call"] == "load_object_in_new_doc"
        assert data["arguments"]["obj_id"] == PARENT_ID
        assert data["arguments"]["child_depths"] == []


# ===========================================================================
# Тесты для PartLoader
# ===========================================================================

class TestPartLoaderWithChildDepths:
    """Тесты PartLoader с параметром child_depths."""

    @patch('service.freecad.part_loader.get_server_instance')
    def test_load_part_to_freecad_with_child_depths(self, mock_get_server):
        """PartLoader передаёт child_depths в сервер."""
        mock_server = MagicMock()
        mock_server.send_message.return_value = True
        mock_get_server.return_value = mock_server

        from service.freecad.part_loader import PartLoader
        loader = PartLoader()

        child_depths = [
            {"child_id": CHILD_ID_1, "parent_child_module_id": PCM_ID_1, "depth": 1},
        ]
        result = loader.load_part_to_freecad(id=PARENT_ID, child_depths=child_depths)

        assert result is True
        mock_server.send_message.assert_called_once()

    @patch('service.freecad.part_loader.get_server_instance')
    def test_load_part_to_freecad_empty_child_depths(self, mock_get_server):
        """PartLoader с пустым child_depths."""
        mock_server = MagicMock()
        mock_server.send_message.return_value = True
        mock_get_server.return_value = mock_server

        from service.freecad.part_loader import PartLoader
        loader = PartLoader()

        result = loader.load_part_to_freecad(id=PARENT_ID, child_depths=[])

        assert result is True
        mock_server.send_message.assert_called_once()
