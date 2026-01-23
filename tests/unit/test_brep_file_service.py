import pytest
from uuid import UUID
from unittest.mock import Mock, patch, MagicMock
from service.brep_file_service import BrepFileService


class TestBrepFileService:

    @patch('service.brep_file_service.save_brep_file')
    @patch('service.brep_file_service.commit_module_changes')
    @patch('service.brep_file_service.Db_session')
    @patch('service.brep_file_service.ModuleVersionRepository')
    def test_save_brep_files_from_dict_success(self, mock_repo_class, mock_db_session_class, mock_commit, mock_save):
        # Setup mocks
        mock_save.return_value = 'path/to/file'
        mock_commit.return_value = 'commit_hash'
        
        mock_db_session = MagicMock()
        mock_db_session_class.return_value.session.return_value.__enter__.return_value = mock_db_session
        
        mock_module = MagicMock()
        mock_module.bounding_contour = MagicMock()
        mock_module.bounding_contour.brep_files = {}
        mock_db_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = mock_module
        
        mock_version = MagicMock()
        mock_repo_instance = MagicMock()
        mock_repo_instance.create_version.return_value = mock_version
        mock_repo_class.return_value = mock_repo_instance
        
        service = BrepFileService()
        result = service.save_brep_files_from_dict(
            UUID('12345678-1234-5678-1234-567812345678'), 
            {'file1': 'content1', 'file2': 'content2'}
        )
        
        assert result == mock_version
        assert mock_save.call_count == 2
        mock_commit.assert_called_once()
        mock_repo_instance.create_version.assert_called_once()

    def test_save_brep_files_from_dict_empty_dict_raises(self):
        service = BrepFileService()
        with pytest.raises(ValueError, match="brep_files_dict не может быть пустым"):
            service.save_brep_files_from_dict(UUID('12345678-1234-5678-1234-567812345678'), {})

    @patch('service.brep_file_service.save_brep_file')
    @patch('service.brep_file_service.commit_module_changes')
    @patch('service.brep_file_service.Db_session')
    @patch('service.brep_file_service.ModuleVersionRepository')
    def test_save_brep_files_from_dict_module_not_found(self, mock_repo_class, mock_db_session_class, mock_commit, mock_save):
        mock_db_session = MagicMock()
        mock_db_session_class.return_value.session.return_value.__enter__.return_value = mock_db_session
        mock_db_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = None
        
        service = BrepFileService()
        with pytest.raises(ValueError, match="Модуль с id .* не найден"):
            service.save_brep_files_from_dict(UUID('12345678-1234-5678-1234-567812345678'), {'file1': 'content1'})

    @patch('service.brep_file_service.save_brep_file')
    @patch('service.brep_file_service.commit_module_changes')
    @patch('service.brep_file_service.Db_session')
    @patch('service.brep_file_service.ModuleVersionRepository')
    def test_save_brep_files_from_dict_no_bounding_contour(self, mock_repo_class, mock_db_session_class, mock_commit, mock_save):
        mock_db_session = MagicMock()
        mock_db_session_class.return_value.session.return_value.__enter__.return_value = mock_db_session
        
        mock_module = MagicMock()
        mock_module.bounding_contour = None
        mock_db_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = mock_module
        
        service = BrepFileService()
        with pytest.raises(ValueError, match="BoundingContour для модуля .* не найден"):
            service.save_brep_files_from_dict(UUID('12345678-1234-5678-1234-567812345678'), {'file1': 'content1'})

    @patch('service.brep_file_service.save_brep_file')
    @patch('service.brep_file_service.commit_module_changes')
    @patch('service.brep_file_service.Db_session')
    @patch('service.brep_file_service.ModuleVersionRepository')
    def test_save_brep_files_from_dict_save_file_error(self, mock_repo_class, mock_db_session_class, mock_commit, mock_save):
        mock_save.side_effect = OSError("Save failed")
        
        service = BrepFileService()
        with pytest.raises(OSError, match="Не удалось сохранить BREP файлы"):
            service.save_brep_files_from_dict(UUID('12345678-1234-5678-1234-567812345678'), {'file1': 'content1'})

    @patch('service.brep_file_service.save_brep_file')
    @patch('service.brep_file_service.commit_module_changes')
    @patch('service.brep_file_service.Db_session')
    @patch('service.brep_file_service.ModuleVersionRepository')
    def test_save_brep_files_from_dict_commit_error(self, mock_repo_class, mock_db_session_class, mock_commit, mock_save):
        mock_save.return_value = 'path/to/file'
        mock_commit.side_effect = RuntimeError("Commit failed")
        
        mock_db_session = MagicMock()
        mock_db_session_class.return_value.session.return_value.__enter__.return_value = mock_db_session
        
        mock_module = MagicMock()
        mock_module.bounding_contour = MagicMock()
        mock_module.bounding_contour.brep_files = {}
        mock_db_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = mock_module
        
        service = BrepFileService()
        with pytest.raises(RuntimeError, match="Не удалось выполнить Git коммит"):
            service.save_brep_files_from_dict(UUID('12345678-1234-5678-1234-567812345678'), {'file1': 'content1'})

    @patch('service.brep_file_service.save_brep_file')
    @patch('service.brep_file_service.commit_module_changes')
    @patch('service.brep_file_service.Db_session')
    @patch('service.brep_file_service.ModuleVersionRepository')
    def test_save_single_brep_file_success(self, mock_repo_class, mock_db_session_class, mock_commit, mock_save):
        # Setup similar to above
        mock_save.return_value = 'path/to/file'
        mock_commit.return_value = 'commit_hash'
        
        mock_db_session = MagicMock()
        mock_db_session_class.return_value.session.return_value.__enter__.return_value = mock_db_session
        
        mock_module = MagicMock()
        mock_module.bounding_contour = MagicMock()
        mock_module.bounding_contour.brep_files = {}
        mock_db_session.query.return_value.options.return_value.filter_by.return_value.first.return_value = mock_module
        
        mock_version = MagicMock()
        mock_repo_instance = MagicMock()
        mock_repo_instance.create_version.return_value = mock_version
        mock_repo_class.return_value = mock_repo_instance
        
        service = BrepFileService()
        result = service.save_single_brep_file(
            UUID('12345678-1234-5678-1234-567812345678'), 
            'file1', 
            b'content'
        )
        
        assert result == mock_version
        mock_save.assert_called_once_with(UUID('12345678-1234-5678-1234-567812345678'), 'file1', b'content')
        mock_commit.assert_called_once()
        mock_repo_instance.create_version.assert_called_once()