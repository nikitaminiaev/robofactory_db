from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from service.git_manager import (
    calculate_brep_files_hash,
    checkout_module_commit,
    commit_module_changes,
    get_module_commit_history,
    init_module_git_repo,
    is_module_git_repo_initialized,
)


class TestGitManager:
    def test_is_module_git_repo_initialized(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        module_root = tmp_path / str(module_id)
        module_root.mkdir(parents=True, exist_ok=True)

        with patch("service.git_manager.get_module_resource_path", return_value=module_root):
            assert not is_module_git_repo_initialized(module_id)
            (module_root / ".git").mkdir(parents=True, exist_ok=True)
            assert is_module_git_repo_initialized(module_id)

    def test_init_module_git_repo_new_repo(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        module_root = tmp_path / str(module_id)
        module_brep_dir = module_root / "brep_files"

        with patch("service.git_manager.get_module_resource_path", return_value=module_root):
            with patch("service.git_manager.get_module_brep_directory", return_value=module_brep_dir):
                with patch("service.git_manager.run", return_value=MagicMock(stdout="ok")) as mock_run:
                    result = init_module_git_repo(module_id)

        assert result == str(module_root)
        assert module_brep_dir.exists()
        assert (module_root / ".gitignore").exists()
        assert (module_brep_dir / ".gitkeep").exists()
        assert mock_run.call_count == 6

    def test_init_module_git_repo_existing_repo(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        module_root = tmp_path / str(module_id)
        module_brep_dir = module_root / "brep_files"
        (module_root / ".git").mkdir(parents=True, exist_ok=True)

        with patch("service.git_manager.get_module_resource_path", return_value=module_root):
            with patch("service.git_manager.get_module_brep_directory", return_value=module_brep_dir):
                with patch("service.git_manager.run") as mock_run:
                    result = init_module_git_repo(module_id)

        assert result == str(module_root)
        mock_run.assert_not_called()

    def test_commit_module_changes_no_changes(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        module_root = tmp_path / str(module_id)
        module_root.mkdir(parents=True, exist_ok=True)

        status_result = MagicMock(stdout="")
        rev_parse_result = MagicMock(stdout="def456\n")
        with patch("service.git_manager.get_module_resource_path", return_value=module_root):
            with patch("service.git_manager.run", side_effect=[MagicMock(), status_result, rev_parse_result]) as mock_run:
                result = commit_module_changes(module_id, "Test commit")

        assert result == "def456"
        assert mock_run.call_count == 3

    def test_commit_module_changes_with_changes(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        module_root = tmp_path / str(module_id)
        module_root.mkdir(parents=True, exist_ok=True)

        status_result = MagicMock(stdout="A test.txt")
        rev_parse_result = MagicMock(stdout="abc123\n")
        side_effect = [MagicMock(), status_result, MagicMock(), rev_parse_result]
        with patch("service.git_manager.get_module_resource_path", return_value=module_root):
            with patch("service.git_manager.run", side_effect=side_effect):
                result = commit_module_changes(module_id, "Test commit")

        assert result == "abc123"

    def test_get_module_commit_history_success(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        module_root = tmp_path / str(module_id)
        module_root.mkdir(parents=True, exist_ok=True)

        git_log_result = MagicMock(stdout="hash1|message1|2023-01-01\nhash2|message2|2023-01-02\n")
        with patch("service.git_manager.get_module_resource_path", return_value=module_root):
            with patch("service.git_manager.run", return_value=git_log_result):
                result = get_module_commit_history(module_id)

        assert len(result) == 2
        assert result[0]["hash"] == "hash1"
        assert result[1]["message"] == "message2"

    def test_checkout_module_commit_empty_hash(self):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        with pytest.raises(ValueError, match="Commit hash cannot be empty"):
            checkout_module_commit(module_id, "")

    def test_checkout_module_commit_git_error(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        module_root = tmp_path / str(module_id)
        module_root.mkdir(parents=True, exist_ok=True)

        with patch("service.git_manager.get_module_resource_path", return_value=module_root):
            with patch(
                "service.git_manager.run",
                side_effect=CalledProcessError(1, "git checkout", stderr="invalid hash"),
            ):
                with pytest.raises(CalledProcessError):
                    checkout_module_commit(module_id, "invalid_hash")

    def test_calculate_brep_files_hash(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        brep_dir = tmp_path / str(module_id) / "brep_files"
        brep_dir.mkdir(parents=True, exist_ok=True)
        (brep_dir / "a.brep").write_text("content-a", encoding="utf-8")
        (brep_dir / "b.brep").write_text("content-b", encoding="utf-8")

        with patch("service.git_manager.get_module_brep_directory", return_value=brep_dir):
            first_hash = calculate_brep_files_hash(module_id)
            second_hash = calculate_brep_files_hash(module_id)

        assert first_hash
        assert first_hash == second_hash