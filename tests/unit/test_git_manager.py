import pytest
from uuid import UUID
from unittest.mock import Mock, patch, MagicMock, call
from service.git_manager import init_module_git_repo, commit_module_changes, get_module_commit_history, checkout_module_commit
from pathlib import Path
import os


class TestGitManager:

    @patch('service.git_manager.os.makedirs')
    @patch('service.git_manager.Path')
    @patch('service.git_manager.run')
    def test_init_module_git_repo_new_repo(self, mock_run, mock_path_class, mock_makedirs):
        # Setup mocks
        mock_repo_path = MagicMock()
        mock_git_dir = MagicMock()
        mock_path_class.return_value = mock_repo_path
        mock_repo_path.__truediv__.return_value = mock_git_dir
        mock_git_dir.exists.return_value = False
        mock_repo_path.__str__.return_value = '/path/to/repo'
        
        # Call function
        result = init_module_git_repo(UUID('12345678-1234-5678-1234-567812345678'))
        
        # Assertions
        assert result == '/path/to/repo'
        mock_path_class.assert_called_once_with('api/resources/brep_files/12345678-1234-5678-1234-567812345678')
        mock_makedirs.assert_called_once_with(mock_repo_path, exist_ok=True)
        assert mock_run.call_count == 3  # init, config user.name, config user.email

    @patch('service.git_manager.os.makedirs')
    @patch('service.git_manager.Path')
    @patch('service.git_manager.run')
    def test_init_module_git_repo_existing_repo(self, mock_run, mock_path_class, mock_makedirs):
        # Setup mocks for existing repo
        mock_repo_path = MagicMock()
        mock_git_dir = MagicMock()
        mock_path_class.return_value = mock_repo_path
        mock_repo_path.__truediv__.return_value = mock_git_dir
        mock_git_dir.exists.return_value = True
        mock_git_dir.is_dir.return_value = True
        mock_repo_path.__str__.return_value = '/path/to/repo'
        
        # Call function
        result = init_module_git_repo(UUID('12345678-1234-5678-1234-567812345678'))
        
        # Assertions
        assert result == '/path/to/repo'
        mock_makedirs.assert_called_once_with(mock_repo_path, exist_ok=True)
        mock_run.assert_not_called()

    @patch('service.git_manager.os.makedirs')
    @patch('service.git_manager.Path')
    @patch('service.git_manager.run')
    def test_init_module_git_repo_git_init_error(self, mock_run, mock_path_class, mock_makedirs):
        # Setup mocks to raise error on git init
        mock_repo_path = MagicMock()
        mock_git_dir = MagicMock()
        mock_path_class.return_value = mock_repo_path
        mock_repo_path.__truediv__.return_value = mock_git_dir
        mock_git_dir.exists.return_value = False
        mock_run.side_effect = Exception("git init failed")
        
        # Call and expect error
        with pytest.raises(Exception, match="git init failed"):
            init_module_git_repo(UUID('12345678-1234-5678-1234-567812345678'))

    @patch('service.git_manager.Path')
    @patch('service.git_manager.run')
    def test_commit_module_changes_with_files(self, mock_run, mock_path_class):
        # Setup mocks
        mock_repo_path = MagicMock()
        mock_file1 = MagicMock()
        mock_file2 = MagicMock()
        mock_path_class.return_value = mock_repo_path
        mock_repo_path.glob.return_value = [mock_file1, mock_file2]
        mock_file1.is_file.return_value = True
        mock_file2.is_file.return_value = True
        mock_file1.name = 'file1.brep'
        mock_file2.name = 'file2.brep'
        
        mock_run.return_value.stdout = 'abc123\n'
        
        # Call function
        result = commit_module_changes(UUID('12345678-1234-5678-1234-567812345678'), 'Test commit')
        
        # Assertions
        assert result == 'abc123'
        mock_path_class.assert_called_once_with('api/resources/brep_files/12345678-1234-5678-1234-567812345678')
        mock_repo_path.glob.assert_called_once_with('*')
        assert mock_run.call_count == 4  # status, add file1, add file2, commit

    @patch('service.git_manager.Path')
    @patch('service.git_manager.run')
    def test_commit_module_changes_no_changes(self, mock_run, mock_path_class):
        # Setup mocks for no files
        mock_repo_path = MagicMock()
        mock_path_class.return_value = mock_repo_path
        mock_repo_path.glob.return_value = []
        
        mock_run.return_value.stdout = 'def456\n'
        
        # Call function
        result = commit_module_changes(UUID('12345678-1234-5678-1234-567812345678'), 'Test commit')
        
        # Assertions
        assert result == 'def456'
        mock_run.assert_called_once()  # Only rev-parse HEAD

    @patch('service.git_manager.Path')
    @patch('service.git_manager.run')
    def test_commit_module_changes_no_files_empty_commit(self, mock_run, mock_path_class):
        # Setup mocks for no files, no commits yet
        mock_repo_path = MagicMock()
        mock_path_class.return_value = mock_repo_path
        mock_repo_path.glob.return_value = []
        
        # First rev-parse fails, then allow-empty commit succeeds
        mock_run.side_effect = [
            Exception("No commits"),  # rev-parse fails
            MagicMock(stdout='ghi789\n')  # allow-empty commit
        ]
        
        # Call function
        result = commit_module_changes(UUID('12345678-1234-5678-1234-567812345678'), 'Test commit')
        
        # Assertions
        assert result == 'ghi789'

    @patch('service.git_manager.Path')
    @patch('service.git_manager.run')
    def test_get_module_commit_history_success(self, mock_run, mock_path_class):
        # Setup mocks
        mock_repo_path = MagicMock()
        mock_path_class.return_value = mock_repo_path
        mock_run.return_value.stdout = 'hash1|message1|2023-01-01\nhash2|message2|2023-01-02\n'
        
        # Call function
        result = get_module_commit_history(UUID('12345678-1234-5678-1234-567812345678'))
        
        # Assertions
        assert len(result) == 2
        assert result[0]['hash'] == 'hash1'
        assert result[0]['message'] == 'message1'
        assert result[1]['hash'] == 'hash2'
        mock_run.assert_called_once()

    @patch('service.git_manager.Path')
    @patch('service.git_manager.run')
    def test_get_module_commit_history_error(self, mock_run, mock_path_class):
        # Setup mocks to raise error
        mock_repo_path = MagicMock()
        mock_path_class.return_value = mock_repo_path
        mock_run.side_effect = Exception("git log failed")
        
        # Call and expect error
        with pytest.raises(Exception, match="git log failed"):
            get_module_commit_history(UUID('12345678-1234-5678-1234-567812345678'))

    @patch('service.git_manager.Path')
    @patch('service.git_manager.run')
    def test_checkout_module_commit_success(self, mock_run, mock_path_class):
        # Setup mocks
        mock_repo_path = MagicMock()
        mock_path_class.return_value = mock_repo_path
        mock_run.return_value = MagicMock()
        
        # Call function
        commit_hash = "abc123def456"
        checkout_module_commit(UUID('12345678-1234-5678-1234-567812345678'), commit_hash)
        
        # Assertions
        mock_path_class.assert_called_once_with('api/resources/brep_files/12345678-1234-5678-1234-567812345678')
        mock_run.assert_called_once_with(
            ["git", "checkout", commit_hash],
            cwd=mock_repo_path,
            check=True,
            capture_output=True,
            text=True
        )

    def test_checkout_module_commit_empty_hash(self):
        # Test with empty commit hash
        with pytest.raises(ValueError, match="Commit hash cannot be empty"):
            checkout_module_commit(UUID('12345678-1234-5678-1234-567812345678'), "")
        
        # Test with whitespace-only commit hash
        with pytest.raises(ValueError, match="Commit hash cannot be empty"):
            checkout_module_commit(UUID('12345678-1234-5678-1234-567812345678'), "   ")
        
        # Test with None-like empty string
        with pytest.raises(ValueError, match="Commit hash cannot be empty"):
            checkout_module_commit(UUID('12345678-1234-5678-1234-567812345678'), "\t\n")

    @patch('service.git_manager.Path')
    @patch('service.git_manager.run')
    def test_checkout_module_commit_git_error(self, mock_run, mock_path_class):
        # Setup mocks to raise git error
        mock_repo_path = MagicMock()
        mock_path_class.return_value = mock_repo_path
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "git checkout", stderr="error: pathspec 'invalid' did not match")
        
        # Call and expect error
        with pytest.raises(CalledProcessError):
            checkout_module_commit(UUID('12345678-1234-5678-1234-567812345678'), "invalid_hash")