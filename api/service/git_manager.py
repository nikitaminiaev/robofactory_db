from subprocess import run, CalledProcessError
from pathlib import Path
from uuid import UUID
import os
import logging
import hashlib
from service.constants import BREP_FILES_PATH

logger = logging.getLogger(__name__)


def calculate_brep_files_hash(module_id: UUID) -> str:
    """
    Вычисляет SHA256 хеш содержимого всех BREP файлов модуля.

    Args:
        module_id: UUID модуля

    Returns:
        SHA256 хеш в виде строки
    """
    repo_path = Path(BREP_FILES_PATH) / str(module_id)

    if not repo_path.exists():
        return ""

    # Собираем все файлы в директории
    files = []
    for file_path in repo_path.rglob('*'):
        if file_path.is_file():
            files.append(file_path)

    # Сортируем файлы для консистентности хеша
    files.sort(key=lambda p: str(p.relative_to(repo_path)))

    hasher = hashlib.sha256()
    for file_path in files:
        try:
            content = file_path.read_bytes()
            hasher.update(content)
            # Добавляем имя файла для отличия файлов с одинаковым содержимым
            hasher.update(str(file_path.relative_to(repo_path)).encode())
        except Exception as e:
            logger.warning(f"Не удалось прочитать файл {file_path}: {e}")

    return hasher.hexdigest()


def init_module_git_repo(module_id: UUID) -> str:
    """
    Инициализирует Git репозиторий для модуля, если он еще не существует.

    Args:
        module_id: UUID модуля

    Returns:
        Путь к репозиторию

    Raises:
        CalledProcessError: Если git init не удался
    """
    repo_path = Path(BREP_FILES_PATH) / str(module_id)

    # Создать директорию если она не существует
    os.makedirs(repo_path, exist_ok=True)

    # Проверить, является ли директория уже git репозиторием
    git_dir = repo_path / ".git"
    if git_dir.exists() and git_dir.is_dir():
        return str(repo_path)

    try:
        run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        # Отключаем использование .gitignore из родительских директорий
        run(["git", "config", "core.excludesFile", "/dev/null"], cwd=repo_path, check=True, capture_output=True)
        # Настраиваем git пользователя (обязательно для коммитов)
        run(["git", "config", "user.name", "RoboFactory System"], cwd=repo_path, check=True, capture_output=True)
        run(["git", "config", "user.email", "system@robofactory.local"], cwd=repo_path, check=True, capture_output=True)
        return str(repo_path)
    except CalledProcessError as e:
        raise CalledProcessError(e.returncode, e.cmd, e.output, e.stderr) from e


def commit_module_changes(module_id: UUID, message: str) -> str:
    """
    Выполняет git add . и git commit для модуля.

    Args:
        module_id: UUID модуля
        message: Сообщение коммита

    Returns:
        Хеш коммита

    Raises:
        CalledProcessError: Если git команды не удались
    """
    repo_path = Path(BREP_FILES_PATH) / str(module_id)

    try:
        # Получить список файлов в директории
        files_in_dir = list(repo_path.glob("*"))
        files_in_dir = [f for f in files_in_dir if f.is_file()]

        if not files_in_dir:
            # Нет файлов для коммита, создаем пустой коммит
            try:
                hash_result = run(["git", "rev-parse", "HEAD"], cwd=repo_path, check=True, capture_output=True, text=True)
                return hash_result.stdout.strip()
            except CalledProcessError:
                # Репозиторий пустой, создадим пустой начальный коммит
                run(["git", "commit", "--allow-empty", "-m", "Initial empty commit"], cwd=repo_path, check=True, capture_output=True, text=True)
                hash_result = run(["git", "rev-parse", "HEAD"], cwd=repo_path, check=True, capture_output=True, text=True)
                return hash_result.stdout.strip()

        # Добавить все файлы по отдельности с --force
        for file_path in files_in_dir:
            run(["git", "add", "--force", file_path.name], cwd=repo_path, check=True, capture_output=True, text=True)

        # Проверить статус после добавления
        status_result = run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)

        if not status_result.stdout.strip():
            # Нет изменений для коммита (файлы уже закоммичены)
            hash_result = run(["git", "rev-parse", "HEAD"], cwd=repo_path, check=True, capture_output=True, text=True)
            return hash_result.stdout.strip()

        # git commit
        result = run(["git", "commit", "-m", message], cwd=repo_path, check=True, capture_output=True, text=True)
        # Получить хеш
        hash_result = run(["git", "rev-parse", "HEAD"], cwd=repo_path, check=True, capture_output=True, text=True)
        return hash_result.stdout.strip()
    except CalledProcessError as e:
        raise CalledProcessError(e.returncode, e.cmd, e.output, e.stderr) from e


def get_module_commit_history(module_id: UUID) -> list[dict[str, str]]:
    """
    Получает историю коммитов для модуля.
    
    Args:
        module_id: UUID модуля
        
    Returns:
        Список словарей с хешем, сообщением и датой
        
    Raises:
        CalledProcessError: Если git log не удался
    """
    repo_path = Path(BREP_FILES_PATH) / str(module_id)
    
    try:
        result = run(["git", "log", "--pretty=format:%H|%s|%ai"], cwd=repo_path, check=True, capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        history = []
        for line in lines:
            if line:
                commit_hash, message, date = line.split('|', 2)
                history.append({"hash": commit_hash, "message": message, "date": date})
        return history
    except CalledProcessError as e:
        raise CalledProcessError(e.returncode, e.cmd, e.output, e.stderr) from e