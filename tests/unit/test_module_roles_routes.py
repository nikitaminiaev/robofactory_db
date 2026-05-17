import pytest
from uuid import UUID, uuid4
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestModuleRolesRoutes:
    """Тесты для API эндпоинтов управления ролями модулей"""

    @pytest.fixture
    def app(self):
        from fastapi import FastAPI
        from routes.module_roles import router

        app = FastAPI()
        app.include_router(router, prefix="/api")
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_get_module_roles_success(self, app, client):
        from routes.module_roles import RoleRepository, RoleResponse

        module_id = uuid4()
        role_id = uuid4()

        mock_role = MagicMock()
        mock_role.id = role_id
        mock_role.name = "parent"
        mock_role.description = "Parent role"

        mock_role_instance = MagicMock()
        mock_role_instance.fetch_module_roles.return_value = [mock_role]

        mock_module_instance = MagicMock()
        mock_module_instance.get_module_by_id.return_value = MagicMock(id=module_id)

        def override_role_repo():
            return mock_role_instance

        def override_module_repo():
            return mock_module_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        app.dependency_overrides[__import__('repository.module_repository', fromlist=['ModuleRepository']).ModuleRepository] = override_module_repo

        try:
            response = client.get(f"/api/modules/{module_id}/roles")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "parent"
        finally:
            app.dependency_overrides.clear()

    def test_get_module_roles_invalid_uuid(self, client):
        response = client.get("/api/modules/invalid-uuid/roles")

        assert response.status_code == 400

    def test_get_module_roles_not_found(self, app, client):
        from routes.module_roles import RoleRepository

        mock_role_instance = MagicMock()
        mock_role_instance.fetch_module_roles.return_value = []

        mock_module_instance = MagicMock()
        mock_module_instance.get_module_by_id.return_value = None

        def override_role_repo():
            return mock_role_instance

        def override_module_repo():
            return mock_module_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        app.dependency_overrides[__import__('repository.module_repository', fromlist=['ModuleRepository']).ModuleRepository] = override_module_repo

        try:
            module_id = uuid4()
            response = client.get(f"/api/modules/{module_id}/roles")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_search_roles_success(self, app, client):
        from routes.module_roles import RoleRepository

        role_id = uuid4()
        mock_role_instance = MagicMock()
        mock_role_instance.search_roles.return_value = [
            {"id": str(role_id), "name": "controller", "description": "Main controller"},
        ]

        def override_role_repo():
            return mock_role_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        try:
            response = client.get("/api/roles?query=cont&limit=5")
            assert response.status_code == 200
            assert response.json() == [
                {"id": str(role_id), "name": "controller", "description": "Main controller"},
            ]
            mock_role_instance.search_roles.assert_called_once_with(query="cont", limit=5)
        finally:
            app.dependency_overrides.clear()

    def test_get_role_details_success(self, app, client):
        from routes.module_roles import RoleRepository

        role_id = uuid4()
        role_details = {
            "id": str(role_id),
            "name": "controller",
            "description": "Main controller",
            "created_ts": None,
            "stream_usages": [],
        }
        mock_role_instance = MagicMock()
        mock_role_instance.get_role_details.return_value = role_details

        def override_role_repo():
            return mock_role_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        try:
            response = client.get(f"/api/roles/{role_id}")
            assert response.status_code == 200
            assert response.json() == role_details
            mock_role_instance.get_role_details.assert_called_once_with(role_id)
        finally:
            app.dependency_overrides.clear()

    def test_get_role_details_invalid_uuid(self, client):
        response = client.get("/api/roles/invalid-uuid")

        assert response.status_code == 400

    def test_get_role_details_not_found(self, app, client):
        from routes.module_roles import RoleRepository

        mock_role_instance = MagicMock()
        mock_role_instance.get_role_details.return_value = None

        def override_role_repo():
            return mock_role_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        try:
            response = client.get(f"/api/roles/{uuid4()}")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_update_role_success(self, app, client):
        from routes.module_roles import RoleRepository

        role_id = uuid4()
        updated_role = {
            "id": str(role_id),
            "name": "updated",
            "description": "Updated description",
            "created_ts": None,
        }
        mock_role_instance = MagicMock()
        mock_role_instance.update_role.return_value = updated_role

        def override_role_repo():
            return mock_role_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        try:
            response = client.patch(
                f"/api/roles/{role_id}",
                json={"name": " updated ", "description": "Updated description"},
            )
            assert response.status_code == 200
            assert response.json() == updated_role
            mock_role_instance.update_role.assert_called_once_with(
                role_id,
                "updated",
                "Updated description",
            )
        finally:
            app.dependency_overrides.clear()

    def test_update_role_empty_name(self, app, client):
        from routes.module_roles import RoleRepository

        mock_role_instance = MagicMock()

        def override_role_repo():
            return mock_role_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        try:
            response = client.patch(
                f"/api/roles/{uuid4()}",
                json={"name": "   ", "description": None},
            )
            assert response.status_code == 400
            mock_role_instance.update_role.assert_not_called()
        finally:
            app.dependency_overrides.clear()

    def test_update_role_not_found(self, app, client):
        from routes.module_roles import RoleRepository

        mock_role_instance = MagicMock()
        mock_role_instance.update_role.return_value = None

        def override_role_repo():
            return mock_role_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        try:
            response = client.patch(
                f"/api/roles/{uuid4()}",
                json={"name": "missing", "description": None},
            )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_delete_role_success(self, app, client):
        from routes.module_roles import RoleRepository

        role_id = uuid4()
        mock_role_instance = MagicMock()
        mock_role_instance.delete_role.return_value = True

        def override_role_repo():
            return mock_role_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        try:
            response = client.delete(f"/api/roles/{role_id}")
            assert response.status_code == 200
            assert response.json() == {"message": "Роль успешно удалена"}
            mock_role_instance.delete_role.assert_called_once_with(role_id)
        finally:
            app.dependency_overrides.clear()

    def test_delete_role_invalid_uuid(self, client):
        response = client.delete("/api/roles/invalid-uuid")

        assert response.status_code == 400

    def test_delete_role_not_found(self, app, client):
        from routes.module_roles import RoleRepository

        mock_role_instance = MagicMock()
        mock_role_instance.delete_role.return_value = False

        def override_role_repo():
            return mock_role_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        try:
            response = client.delete(f"/api/roles/{uuid4()}")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_add_role_by_role_id_success(self, app, client):
        from routes.module_roles import RoleRepository

        module_id = uuid4()
        role_id = uuid4()

        mock_role = MagicMock()
        mock_role.id = role_id
        mock_role.name = "child"
        mock_role.description = "Child role"

        mock_role_instance = MagicMock()
        mock_role_instance.assign_role.return_value = None
        mock_role_instance.fetch_module_roles.return_value = [mock_role]

        mock_module_instance = MagicMock()
        mock_module_instance.get_module_by_id.return_value = MagicMock(id=module_id)

        def override_role_repo():
            return mock_role_instance

        def override_module_repo():
            return mock_module_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        app.dependency_overrides[__import__('repository.module_repository', fromlist=['ModuleRepository']).ModuleRepository] = override_module_repo

        try:
            response = client.post(
                f"/api/modules/{module_id}/roles",
                json={"role_id": str(role_id)}
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "child"
            mock_role_instance.assign_role.assert_called_once_with(module_id, role_id)
        finally:
            app.dependency_overrides.clear()

    def test_add_role_by_name_success(self, app, client):
        from routes.module_roles import RoleRepository

        module_id = uuid4()

        mock_role = MagicMock()
        mock_role.id = uuid4()
        mock_role.name = "new_role"
        mock_role.description = "New role description"

        mock_role_instance = MagicMock()
        mock_role_instance.create_and_assign_role.return_value = mock_role

        mock_module_instance = MagicMock()
        mock_module_instance.get_module_by_id.return_value = MagicMock(id=module_id)

        def override_role_repo():
            return mock_role_instance

        def override_module_repo():
            return mock_module_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        app.dependency_overrides[__import__('repository.module_repository', fromlist=['ModuleRepository']).ModuleRepository] = override_module_repo

        try:
            response = client.post(
                f"/api/modules/{module_id}/roles",
                json={"name": "new_role", "description": "New role description"}
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "new_role"
            mock_role_instance.create_and_assign_role.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_add_role_missing_role_id_and_name(self, app, client):
        from routes.module_roles import RoleRepository

        mock_role_instance = MagicMock()
        mock_module_instance = MagicMock()

        def override_role_repo():
            return mock_role_instance

        def override_module_repo():
            return mock_module_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        app.dependency_overrides[__import__('repository.module_repository', fromlist=['ModuleRepository']).ModuleRepository] = override_module_repo

        try:
            module_id = uuid4()
            response = client.post(
                f"/api/modules/{module_id}/roles",
                json={}
            )

            assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()

    def test_remove_role_success(self, app, client):
        from routes.module_roles import RoleRepository

        module_id = uuid4()
        role_id = uuid4()

        mock_role_instance = MagicMock()
        mock_role_instance.unassign_role.return_value = None

        mock_module_instance = MagicMock()
        mock_module_instance.get_module_by_id.return_value = MagicMock(id=module_id)

        def override_role_repo():
            return mock_role_instance

        def override_module_repo():
            return mock_module_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        app.dependency_overrides[__import__('repository.module_repository', fromlist=['ModuleRepository']).ModuleRepository] = override_module_repo

        try:
            response = client.delete(f"/api/modules/{module_id}/roles/{role_id}")

            assert response.status_code == 200
            mock_role_instance.unassign_role.assert_called_once_with(module_id, role_id)
        finally:
            app.dependency_overrides.clear()

    def test_remove_role_invalid_uuid(self, client):
        response = client.delete("/api/modules/invalid/roles/invalid")

        assert response.status_code == 400

    def test_remove_role_module_not_found(self, app, client):
        from routes.module_roles import RoleRepository

        mock_role_instance = MagicMock()
        mock_module_instance = MagicMock()
        mock_module_instance.get_module_by_id.return_value = None

        def override_role_repo():
            return mock_role_instance

        def override_module_repo():
            return mock_module_instance

        app.dependency_overrides[RoleRepository] = override_role_repo
        app.dependency_overrides[__import__('repository.module_repository', fromlist=['ModuleRepository']).ModuleRepository] = override_module_repo

        try:
            module_id = uuid4()
            role_id = uuid4()
            response = client.delete(f"/api/modules/{module_id}/roles/{role_id}")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestRoleAssignRequest:
    """Тесты для модели RoleAssignRequest"""

    def test_role_assign_request_with_role_id(self):
        from routes.module_roles import RoleAssignRequest

        request = RoleAssignRequest(role_id="12345678-1234-5678-1234-567812345678")
        assert request.role_id == "12345678-1234-5678-1234-567812345678"
        assert request.name is None
        assert request.description is None

    def test_role_assign_request_with_name(self):
        from routes.module_roles import RoleAssignRequest

        request = RoleAssignRequest(name="parent", description="Parent role")
        assert request.name == "parent"
        assert request.description == "Parent role"
        assert request.role_id is None

    def test_role_assign_request_empty(self):
        from routes.module_roles import RoleAssignRequest

        request = RoleAssignRequest()
        assert request.role_id is None
        assert request.name is None
        assert request.description is None


class TestRoleResponse:
    """Тесты для модели RoleResponse"""

    def test_role_response_with_description(self):
        from routes.module_roles import RoleResponse

        response = RoleResponse(
            id="12345678-1234-5678-1234-567812345678",
            name="parent",
            description="Parent role"
        )
        assert response.id == "12345678-1234-5678-1234-567812345678"
        assert response.name == "parent"
        assert response.description == "Parent role"

    def test_role_response_without_description(self):
        from routes.module_roles import RoleResponse

        response = RoleResponse(id="12345678-1234-5678-1234-567812345678", name="child")
        assert response.id == "12345678-1234-5678-1234-567812345678"
        assert response.name == "child"
        assert response.description is None
