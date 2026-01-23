import pytest
from uuid import UUID
from unittest.mock import Mock, patch, MagicMock
from service.module_copier import copy_module_with_roles


class TestModuleCopier:

    @patch('service.module_copier.ModuleVersionRepository')
    @patch('service.module_copier.ModuleRepository')
    def test_copy_module_with_roles_success(self, mock_module_repo_class, mock_version_repo_class):
        # Setup mocks
        mock_module_repo_instance = MagicMock()
        mock_new_module = MagicMock()
        mock_new_module.id = UUID('87654321-4321-8765-4321-876543218765')
        mock_module_repo_instance.copy_module_with_roles.return_value = mock_new_module
        mock_module_repo_class.return_value = mock_module_repo_instance
        
        mock_version_repo_instance = MagicMock()
        mock_version = MagicMock()
        mock_version_repo_instance.create_version_with_git.return_value = mock_version
        mock_version_repo_class.return_value = mock_version_repo_instance
        
        # Call function
        result = copy_module_with_roles(
            module_id=UUID('12345678-1234-5678-1234-567812345678'),
            new_author='test_author',
            version_number='1.0.0',
            description='Test version'
        )
        
        # Assertions
        assert result == mock_new_module
        mock_module_repo_instance.copy_module_with_roles.assert_called_once_with(
            module_id=UUID('12345678-1234-5678-1234-567812345678'),
            new_author='test_author',
            version_number='1.0.0',
            description='Test version'
        )
        mock_version_repo_instance.create_version_with_git.assert_called_once_with(
            module_id=mock_new_module.id,
            version_number='1.0.0',
            description='Test version'
        )

    @patch('service.module_copier.ModuleVersionRepository')
    @patch('service.module_copier.ModuleRepository')
    def test_copy_module_with_roles_module_repo_error(self, mock_module_repo_class, mock_version_repo_class):
        # Setup mock to raise error
        mock_module_repo_instance = MagicMock()
        mock_module_repo_instance.copy_module_with_roles.side_effect = ValueError("Module not found")
        mock_module_repo_class.return_value = mock_module_repo_instance
        
        # Call and expect error
        with pytest.raises(ValueError, match="Module not found"):
            copy_module_with_roles(
                module_id=UUID('12345678-1234-5678-1234-567812345678'),
                new_author='test_author',
                version_number='1.0.0',
                description='Test version'
            )
        
        # Version repo should not be called
        mock_version_repo_class.return_value.create_version_with_git.assert_not_called()

    @patch('service.module_copier.ModuleVersionRepository')
    @patch('service.module_copier.ModuleRepository')
    def test_copy_module_with_roles_version_repo_error(self, mock_module_repo_class, mock_version_repo_class):
        # Setup mocks
        mock_module_repo_instance = MagicMock()
        mock_new_module = MagicMock()
        mock_new_module.id = UUID('87654321-4321-8765-4321-876543218765')
        mock_module_repo_instance.copy_module_with_roles.return_value = mock_new_module
        mock_module_repo_class.return_value = mock_module_repo_instance
        
        mock_version_repo_instance = MagicMock()
        mock_version_repo_instance.create_version_with_git.side_effect = RuntimeError("Git error")
        mock_version_repo_class.return_value = mock_version_repo_instance
        
        # Call and expect error
        with pytest.raises(RuntimeError, match="Git error"):
            copy_module_with_roles(
                module_id=UUID('12345678-1234-5678-1234-567812345678'),
                new_author='test_author',
                version_number='1.0.0',
                description='Test version'
            )