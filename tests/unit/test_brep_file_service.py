import pytest
from uuid import UUID
from unittest.mock import MagicMock, patch
from service.brep_file_service import BrepFileService


class TestBrepFileService:

    def test_save_brep_files_from_dict_empty_dict_raises(self):
        service = BrepFileService()
        with pytest.raises(ValueError, match="brep_files_dict не может быть пустым"):
            service.save_brep_files_from_dict(UUID('12345678-1234-5678-1234-567812345678'), {})

    @patch('service.brep_file_service.save_brep_file')
    def test_save_brep_files_from_dict_save_file_error(self, mock_save):
        mock_save.side_effect = OSError("Save failed")

        service = BrepFileService()
        with pytest.raises(OSError, match="Не удалось сохранить BREP файлы"):
            service.save_brep_files_from_dict(UUID('12345678-1234-5678-1234-567812345678'), {'file1': 'content1'})

    @patch('service.brep_file_service.ModuleVersionRepository')
    @patch('service.brep_file_service.save_brep_file')
    @patch('service.brep_file_service.commit_module_changes')
    @patch('service.brep_file_service.init_module_git_repo')
    @patch('service.brep_file_service.is_module_git_repo_initialized')
    @patch('service.brep_file_service.BoundingContourRepository')
    def test_save_brep_files_from_dict_first_save_creates_initial_version(
        self,
        mock_contour_repo_class,
        mock_is_git_initialized,
        mock_init_repo,
        mock_commit,
        mock_save,
        mock_repo_class
    ):
        mock_save.side_effect = [
            "module/brep_files/file1.brep",
            "module/brep_files/file2.brep",
        ]
        mock_contour_repo = MagicMock()
        mock_contour_repo_class.return_value = mock_contour_repo
        mock_is_git_initialized.return_value = False
        mock_init_repo.return_value = "/repo/path"
        mock_commit.return_value = "commit_hash"

        mock_version = MagicMock()
        mock_repo_instance = MagicMock()
        mock_repo_instance.get_latest_version.return_value = None
        mock_repo_instance.create_version.return_value = mock_version
        mock_repo_class.return_value = mock_repo_instance

        service = BrepFileService()
        result = service.save_brep_files_from_dict(
            UUID("12345678-1234-5678-1234-567812345678"),
            {"file1.brep": "content1", "file2.brep": "content2"},
            "Initial BREP files"
        )

        assert result == mock_version
        assert mock_save.call_count == 2
        mock_contour_repo.update_brep_files.assert_called_once()
        mock_init_repo.assert_called_once()
        mock_commit.assert_called_once()
        mock_repo_instance.create_version.assert_called_once()

    @patch('service.brep_file_service.save_brep_file')
    @patch('service.brep_file_service.ModuleVersionRepository')
    @patch('service.brep_file_service.BoundingContourRepository')
    def test_save_brep_files_from_dict_repeated_save_returns_latest_version(
        self,
        mock_contour_repo_class,
        mock_repo_class,
        mock_save
    ):
        mock_save.return_value = "module/brep_files/file1.brep"
        mock_contour_repo = MagicMock()
        mock_contour_repo_class.return_value = mock_contour_repo

        mock_repo_instance = MagicMock()
        mock_existing_version = MagicMock()
        mock_repo_instance.get_latest_version.return_value = mock_existing_version
        mock_repo_class.return_value = mock_repo_instance

        service = BrepFileService()
        result = service.save_brep_files_from_dict(
            UUID("12345678-1234-5678-1234-567812345678"),
            {"file1.brep": "content1"}
        )

        assert result == mock_existing_version
        mock_save.assert_called_once()
        mock_contour_repo.update_brep_files.assert_called_once()
        mock_repo_instance.create_version.assert_not_called()

    @patch('service.brep_file_service.save_brep_file')
    @patch('service.brep_file_service.ModuleVersionRepository')
    @patch('service.brep_file_service.BoundingContourRepository')
    def test_save_single_brep_file_success(self, mock_contour_repo_class, mock_repo_class, mock_save):
        mock_save.return_value = "module/brep_files/file1.brep"
        mock_contour_repo = MagicMock()
        mock_contour_repo_class.return_value = mock_contour_repo

        mock_version = MagicMock()
        mock_repo_instance = MagicMock()
        mock_repo_instance.get_latest_version.return_value = mock_version
        mock_repo_class.return_value = mock_repo_instance

        service = BrepFileService()
        result = service.save_single_brep_file(
            UUID("12345678-1234-5678-1234-567812345678"),
            "file1.brep",
            b"content",
        )

        assert result == mock_version
        mock_save.assert_called_once()
        mock_contour_repo.update_brep_files.assert_called_once()