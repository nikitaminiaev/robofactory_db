from subprocess import run, CalledProcessError
from pathlib import Path
from uuid import UUID
import os
import logging
import hashlib
from service.constants import get_module_brep_directory, get_module_resource_path

logger = logging.getLogger(__name__)


def calculate_brep_files_hash(module_id: UUID) -> str:
    """
    Вычисляет SHA256 хеш содержимого всех BREP файлов модуля.

    Args:
        module_id: UUID модуля

    Returns:
        SHA256 хеш в виде строки
    """
    repo_path = get_module_brep_directory(module_id)

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


def is_module_git_repo_initialized(module_id: UUID) -> bool:
    git_dir = get_module_resource_path(module_id) / ".git"
    return git_dir.exists() and git_dir.is_dir()


def _write_initial_git_files(repo_path: Path) -> None:
    gitignore_content = "\n".join(
        [
            "*",
            "!.gitignore",
            "!*.scad",
            "",
        ]
    )
    (repo_path / ".gitignore").write_text(gitignore_content, encoding="utf-8")

    brep_dir = repo_path / "brep_files"
    brep_dir.mkdir(parents=True, exist_ok=True)

    stl_dir = repo_path / "stl_files"
    stl_dir.mkdir(parents=True, exist_ok=True)


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
    repo_path = get_module_resource_path(module_id)
    brep_dir = get_module_brep_directory(module_id)

    # Создать директории модуля если они не существуют
    os.makedirs(repo_path, exist_ok=True)
    os.makedirs(brep_dir, exist_ok=True)

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
        _write_initial_git_files(repo_path)
        run(["git", "add", ".gitignore"], cwd=repo_path, check=True, capture_output=True)
        run(["git", "commit", "-m", "Initial repository setup"], cwd=repo_path, check=True, capture_output=True)
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
    repo_path = get_module_resource_path(module_id)

    try:
        run(["git", "add", "--all"], cwd=repo_path, check=True, capture_output=True, text=True)
        status_result = run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
        if not status_result.stdout.strip():
            hash_result = run(["git", "rev-parse", "HEAD"], cwd=repo_path, check=True, capture_output=True, text=True)
            return hash_result.stdout.strip()

        run(["git", "commit", "-m", message], cwd=repo_path, check=True, capture_output=True, text=True)
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
    repo_path = get_module_resource_path(module_id)
    
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


def get_module_git_diff(module_id: UUID) -> str:
    """
    Возвращает git diff HEAD — все незакоммиченные изменения относительно последнего коммита.

    Args:
        module_id: UUID модуля

    Returns:
        Строка с диффом (пустая, если нет изменений)
    """
    repo_path = get_module_resource_path(module_id)

    if not (repo_path / ".git").exists():
        return ""

    try:
        result = run(
            ["git", "diff", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except CalledProcessError:
        return ""


def _ensure_on_branch(repo_path: Path) -> None:
    """
    Если репозиторий в detached HEAD, переключается обратно на основную ветку.
    """
    result = run(["git", "branch", "--show-current"], cwd=repo_path, capture_output=True, text=True)
    if result.stdout.strip():
        return

    for branch in ("master", "main"):
        r = run(["git", "checkout", branch], cwd=repo_path, capture_output=True, text=True)
        if r.returncode == 0:
            return


def checkout_module_commit(module_id: UUID, commit_hash: str) -> None:
    """
    Восстанавливает файлы рабочего дерева до состояния указанного коммита,
    не перемещая HEAD и не входя в detached HEAD.

    Использует `git checkout <hash> -- .` вместо `git checkout <hash>`,
    чтобы история коммитов оставалась нетронутой.

    Args:
        module_id: UUID модуля
        commit_hash: Хеш коммита для восстановления файлов

    Raises:
        CalledProcessError: Если git команды не удались
        ValueError: Если commit_hash пустой или невалидный
    """
    if not commit_hash or not commit_hash.strip():
        raise ValueError("Commit hash cannot be empty")

    repo_path = get_module_resource_path(module_id)

    try:
        # Если были в detached HEAD от предыдущего checkout — возвращаемся на ветку
        _ensure_on_branch(repo_path)
        # Восстанавливаем файлы без перемещения HEAD
        run(["git", "checkout", commit_hash, "--", "."], cwd=repo_path, check=True, capture_output=True, text=True)
    except CalledProcessError as e:
        raise CalledProcessError(e.returncode, e.cmd, e.output, e.stderr) from e