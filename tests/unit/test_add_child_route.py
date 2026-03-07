"""
Тест бэкенд-части функциональности кнопки "Add Child" на странице Module Details.

Баг (исправлен в object-details.js): функция addNewRelationToList использовала
document.getElementById('childsList') вместо document.getElementById('childrenList'),
из-за чего list оказывался null и appendChild падал без видимой ошибки.

После исправления фронтенд правильно отправляет PATCH /api/basic_object/{id}
с полем added_children. Данный тест покрывает именно этот маршрут.

Для мокирования зависимостей FastAPI используется app.dependency_overrides
(а не @patch), так как FastAPI захватывает ссылку на класс зависимости
при регистрации маршрута, а не при вызове.
"""
import pytest
from uuid import UUID
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.create_basic_object import router
from repository.module_repository import ModuleRepository
from repository.role_repository import RoleRepository


MODULE_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
CHILD_ID  = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


@pytest.fixture(scope="module")
def app():
    application = FastAPI()
    application.include_router(router)
    return application


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


def _make_module_mock(module_id: str = MODULE_ID) -> MagicMock:
    """Создаёт мок объекта Module с заданным id."""
    mock_module = MagicMock()
    mock_module.id = UUID(module_id)
    mock_module.bounding_contour = MagicMock()
    return mock_module


def _make_repo_mock(module_mock: MagicMock) -> MagicMock:
    """Создаёт мок ModuleRepository, возвращающий заданный модуль."""
    mock_repo = MagicMock()
    mock_repo.get_module_for_update.return_value = module_mock
    mock_repo.add_child_relation.return_value = None
    return mock_repo


class TestAddChildRoute:
    """Тесты маршрута PATCH /api/basic_object/{id} для добавления дочерних модулей."""

    def test_add_child_success(self, app, client):
        """Успешное добавление ребёнка — add_child_relation вызывается один раз."""
        module_mock = _make_module_mock()
        repo_mock = _make_repo_mock(module_mock)

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository] = lambda: MagicMock()

        try:
            payload = {
                "added_children": [
                    {
                        "id": CHILD_ID,
                        "coordinates": {"x": 0, "y": 0, "z": 0, "rx": 0, "ry": 0, "rz": 0},
                    }
                ]
            }
            response = client.patch(f"/api/basic_object/{MODULE_ID}", json=payload)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["ok"] is True

        repo_mock.add_child_relation.assert_called_once()
        call_kwargs = repo_mock.add_child_relation.call_args.kwargs
        assert call_kwargs["parent_id"] == UUID(MODULE_ID)
        assert call_kwargs["child_id"] == UUID(CHILD_ID)

    def test_add_child_module_not_found(self, app, client):
        """Если модуль не найден — маршрут не вызывает add_child_relation."""
        repo_mock = MagicMock()
        repo_mock.get_module_for_update.return_value = None

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository] = lambda: MagicMock()

        try:
            response = client.patch(
                f"/api/basic_object/{MODULE_ID}",
                json={"added_children": [{"id": CHILD_ID}]},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code != 200
        repo_mock.add_child_relation.assert_not_called()

    def test_add_multiple_children(self, app, client):
        """Несколько детей в одном запросе — add_child_relation вызывается для каждого."""
        child_ids = [
            "cccccccc-cccc-cccc-cccc-cccccccccccc",
            "dddddddd-dddd-dddd-dddd-dddddddddddd",
        ]
        module_mock = _make_module_mock()
        repo_mock = _make_repo_mock(module_mock)

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository] = lambda: MagicMock()

        try:
            payload = {"added_children": [{"id": cid} for cid in child_ids]}
            response = client.patch(f"/api/basic_object/{MODULE_ID}", json=payload)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert repo_mock.add_child_relation.call_count == len(child_ids)

        called_child_ids = [
            str(call.kwargs["child_id"])
            for call in repo_mock.add_child_relation.call_args_list
        ]
        assert set(called_child_ids) == set(child_ids)

    def test_add_child_invalid_uuid(self, app, client):
        """Невалидный UUID модуля — маршрут возвращает ошибку без обращения к репозиторию."""
        repo_mock = MagicMock()

        app.dependency_overrides[ModuleRepository] = lambda: repo_mock
        app.dependency_overrides[RoleRepository] = lambda: MagicMock()

        try:
            response = client.patch(
                "/api/basic_object/not-a-uuid",
                json={"added_children": [{"id": CHILD_ID}]},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code in (422, 500)
        repo_mock.add_child_relation.assert_not_called()
