"""
Константы проекта RoboFactory Database.
"""

from pathlib import Path
from uuid import UUID

# Базовые директории (абсолютные, стабильные при reload)
BASE_DIR = Path(__file__).resolve().parents[1]
MODULE_RESOURCES_PATH = BASE_DIR / "resources"
BREP_FILES_DIRNAME = "brep_files"

# Legacy-константа сохранена для обратной совместимости импортов.
BREP_FILES_PATH = str(MODULE_RESOURCES_PATH / BREP_FILES_DIRNAME)


def get_module_resource_path(module_id: UUID) -> Path:
    return MODULE_RESOURCES_PATH / str(module_id)


def get_module_brep_directory(module_id: UUID) -> Path:
    return get_module_resource_path(module_id) / BREP_FILES_DIRNAME


def build_brep_relative_path(module_id: UUID, filename: str) -> str:
    return f"{module_id}/{BREP_FILES_DIRNAME}/{filename}"


def resolve_brep_absolute_path(relative_path: str) -> Path:
    if not relative_path:
        return MODULE_RESOURCES_PATH

    candidate_new = MODULE_RESOURCES_PATH / relative_path
    if candidate_new.exists():
        return candidate_new

    candidate_old = MODULE_RESOURCES_PATH / BREP_FILES_DIRNAME / relative_path
    if candidate_old.exists():
        return candidate_old

    return candidate_new