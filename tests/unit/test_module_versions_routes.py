import pytest
from uuid import UUID
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException


class TestModuleVersionsRoutes:
    """Тесты для API endpoints модуля версионирования"""

    @pytest.fixture
    def app(self):
        """Создание тестового приложения FastAPI"""
        from fastapi import FastAPI
        from routes.module_versions import router
        
        app = FastAPI()
        app.include_router(router, prefix="/api")
        return app

    @pytest.fixture
    def client(self, app):
        """Создание тестового клиента"""
        from fastapi.testclient import TestClient
        return TestClient(app)

    @patch('routes.module_versions.checkout_module_commit')
    def test_checkout_module_success(self, mock_checkout, client):
        """Тест успешного checkout"""
        # Setup
        mock_checkout.return_value = None
        module_id = "12345678-1234-5678-1234-567812345678"
        commit_hash = "abc123def456"
        
        # Call
        response = client.post(
            f"/api/modules/{module_id}/checkout",
            json={"commit_hash": commit_hash}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "commit_hash" in data
        assert data["commit_hash"] == commit_hash
        mock_checkout.assert_called_once()

    @patch('routes.module_versions.checkout_module_commit')
    def test_checkout_module_invalid_uuid(self, mock_checkout, client):
        """Тест checkout с невалидным UUID"""
        # Call
        response = client.post(
            "/api/modules/invalid-uuid/checkout",
            json={"commit_hash": "abc123"}
        )
        
        # Assertions - invalid UUID returns 400 before reaching checkout
        assert response.status_code == 400
        mock_checkout.assert_not_called()

    @patch('routes.module_versions.checkout_module_commit')
    def test_checkout_module_empty_commit_hash(self, mock_checkout, client):
        """Тест checkout с пустым commit_hash"""
        # Setup
        from subprocess import CalledProcessError
        mock_checkout.side_effect = ValueError("Commit hash cannot be empty")
        module_id = "12345678-1234-5678-1234-567812345678"
        
        # Call
        response = client.post(
            f"/api/modules/{module_id}/checkout",
            json={"commit_hash": ""}
        )
        
        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @patch('routes.module_versions.checkout_module_commit')
    def test_checkout_module_git_error(self, mock_checkout, client):
        """Тест checkout при ошибке git"""
        # Setup
        from subprocess import CalledProcessError
        mock_checkout.side_effect = CalledProcessError(
            1, "git checkout", stderr="error: pathspec did not match"
        )
        module_id = "12345678-1234-5678-1234-567812345678"
        
        # Call
        response = client.post(
            f"/api/modules/{module_id}/checkout",
            json={"commit_hash": "invalid_hash"}
        )
        
        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Ошибка при checkout" in data["detail"]


class TestCheckoutRequestModel:
    """Тесты для модели CheckoutRequest"""

    def test_checkout_request_valid(self):
        """Тест создания валидного запроса"""
        from routes.module_versions import CheckoutRequest
        
        request = CheckoutRequest(commit_hash="abc123def456")
        assert request.commit_hash == "abc123def456"

    def test_checkout_request_empty_hash(self):
        """Тест создания запроса с пустым хешем"""
        from routes.module_versions import CheckoutRequest
        
        request = CheckoutRequest(commit_hash="")
        assert request.commit_hash == ""

    def test_checkout_request_missing_field(self):
        """Тест создания запроса без обязательного поля"""
        from routes.module_versions import CheckoutRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            CheckoutRequest()  # type: ignore


class TestCreateModuleVersion:
    """Тесты для POST /modules/{module_id}/versions"""

    @pytest.fixture
    def app(self):
        from fastapi import FastAPI
        from routes.module_versions import router
        from repository.module_version_repository import ModuleVersionRepository
        from repository.module_repository import ModuleRepository
        app = FastAPI()
        app.include_router(router, prefix="/api")
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_create_version_without_git(self, app, client):
        from repository.module_version_repository import ModuleVersionRepository
        from repository.module_repository import ModuleRepository

        mock_version_instance = MagicMock()
        mock_module_instance = MagicMock()

        mock_module_instance.get_children_coordinates.return_value = []
        mock_version_instance.create_version.return_value = MagicMock(
            id="v123",
            module_id="12345678-1234-5678-1234-567812345678",
            version_number="1.0",
            description="Test",
            commit_hash=None,
            git_repo_path=None,
            is_released=False,
            created_ts=None,
            version_metadata=None
        )

        def override_version_repo():
            return mock_version_instance

        def override_module_repo():
            return mock_module_instance

        app.dependency_overrides[ModuleVersionRepository] = override_version_repo
        app.dependency_overrides[ModuleRepository] = override_module_repo

        try:
            module_id = "12345678-1234-5678-1234-567812345678"
            response = client.post(
                f"/api/modules/{module_id}/versions",
                json={"version_number": "1.0", "description": "Test", "is_released": False, "make_git_commit": False}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["version_number"] == "1.0"
            mock_version_instance.create_version.assert_called_once()
            call_kwargs = mock_version_instance.create_version.call_args.kwargs
            assert call_kwargs["commit_hash"] is None
        finally:
            app.dependency_overrides.clear()

    @patch('routes.module_versions.release_commit_module')
    @patch('routes.module_versions.is_module_git_repo_initialized')
    @patch('routes.module_versions.init_module_git_repo')
    def test_create_version_with_release(self, mock_init, mock_is_init, mock_release, app, client):
        from repository.module_version_repository import ModuleVersionRepository
        from repository.module_repository import ModuleRepository

        mock_version_instance = MagicMock()
        mock_module_instance = MagicMock()

        mock_module_instance.get_children_coordinates.return_value = []
        mock_is_init.return_value = False
        mock_init.return_value = "/path/to/repo"
        mock_release.return_value = "abc123"

        mock_version_instance.create_version.return_value = MagicMock(
            id="v123",
            module_id="12345678-1234-5678-1234-567812345678",
            version_number="1.0",
            description="Release 1.0",
            commit_hash="abc123",
            git_repo_path="/path/to/repo",
            is_released=True,
            created_ts=None,
            version_metadata=None
        )

        def override_version_repo():
            return mock_version_instance

        def override_module_repo():
            return mock_module_instance

        app.dependency_overrides[ModuleVersionRepository] = override_version_repo
        app.dependency_overrides[ModuleRepository] = override_module_repo

        try:
            module_id = "12345678-1234-5678-1234-567812345678"
            response = client.post(
                f"/api/modules/{module_id}/versions",
                json={"version_number": "1.0", "description": "Release 1.0", "is_released": True, "make_git_commit": False}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_released"] is True
            mock_release.assert_called_once()
            mock_init.assert_called_once()
        finally:
            app.dependency_overrides.clear()


class TestUpdateModuleVersion:
    """Тесты для PATCH /modules/{module_id}/versions/{version_id}"""

    @pytest.fixture
    def app(self):
        from fastapi import FastAPI
        from routes.module_versions import router
        app = FastAPI()
        app.include_router(router, prefix="/api")
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_update_version_success(self, app, client):
        from repository.module_version_repository import ModuleVersionRepository

        mock_instance = MagicMock()
        mock_instance.update_version.return_value = MagicMock(
            id="v123",
            module_id="12345678-1234-5678-1234-567812345678",
            version_number="2.0",
            description="Updated",
            commit_hash="abc",
            git_repo_path="/repo",
            is_released=True,
            created_ts=None,
            version_metadata=None
        )

        def override_repo():
            return mock_instance

        app.dependency_overrides[ModuleVersionRepository] = override_repo

        try:
            module_id = "12345678-1234-5678-1234-567812345678"
            version_id = "87654321-4321-8765-4321-876543218765"
            response = client.patch(
                f"/api/modules/{module_id}/versions/{version_id}",
                json={"version_number": "2.0", "description": "Updated", "is_released": True}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["version_number"] == "2.0"
        finally:
            app.dependency_overrides.clear()

    def test_update_version_not_found(self, app, client):
        from repository.module_version_repository import ModuleVersionRepository

        mock_instance = MagicMock()
        mock_instance.update_version.side_effect = ValueError("Версия не найдена")

        def override_repo():
            return mock_instance

        app.dependency_overrides[ModuleVersionRepository] = override_repo

        try:
            module_id = "12345678-1234-5678-1234-567812345678"
            version_id = "87654321-4321-8765-4321-876543218765"
            response = client.patch(
                f"/api/modules/{module_id}/versions/{version_id}",
                json={"version_number": "2.0"}
            )

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestModuleVersionDTO:
    """Тесты для схем ModuleVersionCreateDTO и ModuleVersionUpdateDTO"""

    def test_create_dto_defaults(self):
        from schemas.module_version_dto import ModuleVersionCreateDTO
        dto = ModuleVersionCreateDTO(version_number="1.0", description="Test")
        assert dto.version_number == "1.0"
        assert dto.is_released is False
        assert dto.make_git_commit is False

    def test_update_dto_optional_fields(self):
        from schemas.module_version_dto import ModuleVersionUpdateDTO
        dto = ModuleVersionUpdateDTO()
        assert dto.version_number is None
        assert dto.description is None
        assert dto.is_released is None
