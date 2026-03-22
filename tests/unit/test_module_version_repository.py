import pytest
from uuid import UUID
from unittest.mock import MagicMock, patch
from repository.module_version_repository import ModuleVersionRepository


class TestModuleVersionRepository:

    @patch('repository.base_repository.Db_session')
    def test_get_by_module_id(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_versions = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_versions

        repo = ModuleVersionRepository()
        result = repo.get_by_module_id(UUID('12345678-1234-5678-1234-567812345678'))

        assert result == mock_versions

    @patch('repository.base_repository.Db_session')
    def test_get_latest_version_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_version = MagicMock()
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = mock_version

        repo = ModuleVersionRepository()
        result = repo.get_latest_version(UUID('12345678-1234-5678-1234-567812345678'))

        assert result == mock_version

    @patch('repository.base_repository.Db_session')
    def test_get_latest_version_not_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None

        repo = ModuleVersionRepository()
        result = repo.get_latest_version(UUID('12345678-1234-5678-1234-567812345678'))

        assert result is None

    @patch('repository.base_repository.Db_session')
    def test_create_version(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_version = MagicMock()
        mock_db.add.return_value = mock_version

        repo = ModuleVersionRepository()
        result = repo.create_version(
            UUID('12345678-1234-5678-1234-567812345678'),
            "1.0.0",
            "Test version",
            "abc123",
            "file_hash",
            "/path/to/repo",
            True
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('repository.base_repository.Db_session')
    def test_update_version_is_released_success(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_version = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_version

        repo = ModuleVersionRepository()
        result = repo.update_version_is_released(UUID('12345678-1234-5678-1234-567812345678'), True)

        assert mock_version.is_released is True
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('repository.base_repository.Db_session')
    def test_update_version_is_released_not_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        repo = ModuleVersionRepository()
        with pytest.raises(ValueError, match="Version not found"):
            repo.update_version_is_released(UUID('12345678-1234-5678-1234-567812345678'), True)

    @patch('repository.module_version_repository.init_module_git_repo')
    @patch('repository.module_version_repository.commit_module_changes')
    @patch('repository.base_repository.Db_session')
    def test_create_version_with_git_new_repo(self, mock_db_session_class, mock_commit, mock_init):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        mock_init.return_value = "/path/to/repo"
        mock_commit.return_value = "abc123"

        mock_version = MagicMock()
        mock_db.add.return_value = mock_version

        repo = ModuleVersionRepository()
        result = repo.create_version_with_git(
            UUID('12345678-1234-5678-1234-567812345678'),
            "1.0.0",
            "Test version"
        )

        mock_init.assert_called_once()
        mock_commit.assert_called_once()
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @patch('repository.module_version_repository.commit_module_changes')
    @patch('repository.base_repository.Db_session')
    def test_create_version_with_git_existing_repo(self, mock_db_session_class, mock_commit):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_existing = MagicMock()
        mock_existing.git_repo_path = "/path/to/repo"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_existing

        mock_commit.return_value = "abc123"

        mock_version = MagicMock()
        mock_db.add.return_value = mock_version

        repo = ModuleVersionRepository()
        result = repo.create_version_with_git(
            UUID('12345678-1234-5678-1234-567812345678'),
            "1.0.0",
            "Test version"
        )

        mock_commit.assert_called_once()
        mock_db.add.assert_called()

    @patch('repository.base_repository.Db_session')
    def test_create_version_with_metadata(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_version = MagicMock()
        mock_db.add.return_value = mock_version

        repo = ModuleVersionRepository()
        metadata = {"children": [{"id": "child1", "x": 10, "y": 20}]}
        result = repo.create_version(
            UUID('12345678-1234-5678-1234-567812345678'),
            "1.0.0",
            "Test version",
            version_metadata=metadata
        )

        mock_db.add.assert_called_once()
        call_args = mock_db.add.call_args[0][0]
        assert call_args.version_metadata == metadata

    @patch('repository.base_repository.Db_session')
    def test_update_version_success(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_version = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_version

        repo = ModuleVersionRepository()
        result = repo.update_version(
            UUID('12345678-1234-5678-1234-567812345678'),
            version_number="2.0.0",
            description="Updated description",
            is_released=True
        )

        assert mock_version.version_number == "2.0.0"
        assert mock_version.description == "Updated description"
        assert mock_version.is_released is True
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('repository.base_repository.Db_session')
    def test_update_version_not_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        repo = ModuleVersionRepository()
        with pytest.raises(ValueError, match="Версия не найдена"):
            repo.update_version(UUID('12345678-1234-5678-1234-567812345678'), version_number="2.0.0")

    @patch('repository.base_repository.Db_session')
    def test_update_version_ignores_disallowed_fields(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_version = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_version

        repo = ModuleVersionRepository()
        repo.update_version(
            UUID('12345678-1234-5678-1234-567812345678'),
            version_number="2.0.0",
            id="fake-id"
        )

        assert mock_version.version_number == "2.0.0"

    @patch('repository.base_repository.Db_session')
    def test_update_version_skips_none_values(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_version = MagicMock()
        mock_version.version_number = "1.0.0"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_version

        repo = ModuleVersionRepository()
        repo.update_version(
            UUID('12345678-1234-5678-1234-567812345678'),
            version_number=None,
            description="New description"
        )

        assert mock_version.version_number == "1.0.0"
        assert mock_version.description == "New description"
