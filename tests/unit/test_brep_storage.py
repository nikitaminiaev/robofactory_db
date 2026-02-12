from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest

from service.brep_storage import create_module_brep_directory, delete_module_brep_directory, save_brep_file


class TestBrepStorage:
    def test_create_module_brep_directory_success(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        module_brep_dir = tmp_path / "module" / "brep_files"

        with patch("service.brep_storage.get_module_brep_directory", return_value=module_brep_dir):
            result = create_module_brep_directory(module_id)

        assert result == str(module_brep_dir)
        assert module_brep_dir.exists()

    def test_create_module_brep_directory_os_error(self):
        module_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("service.brep_storage.get_module_brep_directory", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Не удалось создать директорию"):
                create_module_brep_directory(module_id)

    def test_save_brep_file_success(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        module_brep_dir = tmp_path / str(module_id) / "brep_files"

        with patch("service.brep_storage.get_module_brep_directory", return_value=module_brep_dir):
            result = save_brep_file(module_id, "test.brep", b"file content")

        assert result == "12345678-1234-5678-1234-567812345678/brep_files/test.brep"
        assert (module_brep_dir / "test.brep").read_bytes() == b"file content"

    def test_save_brep_file_os_error(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        module_brep_dir = tmp_path / str(module_id) / "brep_files"
        module_brep_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(Path, "write_bytes", side_effect=OSError("Write failed")):
            with patch("service.brep_storage.get_module_brep_directory", return_value=module_brep_dir):
                with pytest.raises(OSError, match="Не удалось сохранить файл"):
                    save_brep_file(module_id, "test.brep", b"file content")

    def test_delete_module_brep_directory_success(self, tmp_path: Path):
        module_id = UUID("12345678-1234-5678-1234-567812345678")
        module_root_dir = tmp_path / str(module_id)
        (module_root_dir / "brep_files").mkdir(parents=True, exist_ok=True)
        (module_root_dir / "brep_files" / "a.brep").write_text("x", encoding="utf-8")

        with patch("service.brep_storage.get_module_resource_path", return_value=module_root_dir):
            delete_module_brep_directory(module_id)

        assert not module_root_dir.exists()