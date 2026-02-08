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
        
        # Assertions
        assert response.status_code == 500
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
