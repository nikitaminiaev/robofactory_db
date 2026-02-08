"""
Константы проекта RoboFactory Database.
"""

from pathlib import Path

# Путь к директории с BREP файлами (абсолютный, стабильный при reload)
BASE_DIR = Path(__file__).resolve().parents[1]
BREP_FILES_PATH = str(BASE_DIR / "resources" / "brep_files")