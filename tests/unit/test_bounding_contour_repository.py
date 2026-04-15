import pytest
from uuid import UUID
from unittest.mock import MagicMock, patch, mock_open, call
from pathlib import Path
from repository.bounding_contour_repository import BoundingContourRepository


class TestBoundingContourRepository:

    @patch('repository.base_repository.Db_session')
    def test_get_by_module_id_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_contour = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_contour

        repo = BoundingContourRepository()
        result = repo.get_by_module_id(UUID('12345678-1234-5678-1234-567812345678'))

        assert result == mock_contour

    @patch('repository.base_repository.Db_session')
    def test_get_by_module_id_not_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        repo = BoundingContourRepository()
        result = repo.get_by_module_id(UUID('12345678-1234-5678-1234-567812345678'))

        assert result is None

    @patch('repository.base_repository.Db_session')
    def test_update_brep_files(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_contour = MagicMock()
        mock_contour.brep_files = {"old.brep": "/path/to/old.brep"}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_contour

        repo = BoundingContourRepository()
        result = repo.update_brep_files(
            UUID('12345678-1234-5678-1234-567812345678'),
            {"new.brep": "/path/to/new.brep"}
        )

        assert "old.brep" in result
        assert "new.brep" in result
        mock_db.add.assert_called()
        mock_db.flush.assert_called()
        mock_db.commit.assert_called()

    @patch('repository.base_repository.Db_session')
    def test_update_brep_files_not_found(self, mock_db_session_class):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        repo = BoundingContourRepository()
        with pytest.raises(ValueError, match="BoundingContour for module"):
            repo.update_brep_files(
                UUID('12345678-1234-5678-1234-567812345678'),
                {"new.brep": "/path/to/new.brep"}
            )

    @patch('service.brep_storage.save_brep_file')
    @patch('service.constants.resolve_brep_absolute_path')
    @patch('repository.base_repository.Db_session')
    def test_copy_bounding_contour_with_session(self, mock_db_session_class, mock_resolve, mock_save):
        mock_db = MagicMock()

        mock_original = MagicMock()
        mock_original.brep_files = {"file1.brep": "relative/path/file1.brep"}
        mock_original.is_assembly = True
        mock_original.is_shell = False
        mock_original.parent_id = None

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_original

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_bytes.return_value = b"brep data"
        mock_resolve.return_value = mock_path

        mock_save.return_value = "new/relative/path"

        repo = BoundingContourRepository()
        result = repo.copy_bounding_contour(
            UUID('12345678-1234-5678-1234-567812345678'),
            UUID('87654321-4321-8765-4321-876543218765'),
            mock_db
        )

        assert result is not None
        mock_db.add.assert_called()

    @patch('service.brep_storage.save_brep_file')
    @patch('service.constants.resolve_brep_absolute_path')
    @patch('repository.base_repository.Db_session')
    def test_copy_bounding_contour_original_not_found(self, mock_db_session_class, mock_resolve, mock_save):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        repo = BoundingContourRepository()
        result = repo.copy_bounding_contour(
            UUID('12345678-1234-5678-1234-567812345678'),
            UUID('87654321-4321-8765-4321-876543218765')
        )

        assert result is None
        mock_db.add.assert_not_called()

    @patch('service.brep_storage.save_brep_file')
    @patch('service.constants.resolve_brep_absolute_path')
    @patch('repository.base_repository.Db_session')
    def test_copy_bounding_contour_file_not_exists(self, mock_db_session_class, mock_resolve, mock_save):
        mock_db_session_instance = MagicMock()
        mock_db_session_class.return_value = mock_db_session_instance
        mock_db = MagicMock()
        mock_db_session_instance.session.return_value.__enter__.return_value = mock_db

        mock_original = MagicMock()
        mock_original.brep_files = {"file1.brep": "relative/path/file1.brep"}
        mock_original.is_assembly = False
        mock_original.is_shell = True
        mock_original.parent_id = UUID('11111111-1111-1111-1111-111111111111')

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_original

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        mock_resolve.return_value = mock_path

        repo = BoundingContourRepository()
        result = repo.copy_bounding_contour(
            UUID('12345678-1234-5678-1234-567812345678'),
            UUID('87654321-4321-8765-4321-876543218765')
        )

        mock_save.assert_not_called()
