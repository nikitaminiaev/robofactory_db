from subprocess import run, CalledProcessError
from pathlib import Path
from uuid import UUID
import os
import shutil
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
        _ensure_on_branch(repo_path)
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


def _get_main_branch(repo_path: Path) -> str:
    """
    Возвращает имя основной ветки (master/main).
    Если находимся в detached HEAD, всё равно возвращает имя ветки.
    """
    branch_result = run(["git", "branch", "--show-current"], cwd=repo_path, capture_output=True, text=True)
    branch = branch_result.stdout.strip()
    if branch:
        return branch

    # Detached HEAD — ищем существующую ветку
    branches_result = run(["git", "branch"], cwd=repo_path, capture_output=True, text=True)
    for candidate in ("master", "main"):
        if candidate in branches_result.stdout:
            return candidate

    return "HEAD"


def get_module_head_hash(module_id: UUID) -> str:
    """
    Возвращает хеш текущего git HEAD (реальная позиция HEAD в репозитории).

    Args:
        module_id: UUID модуля

    Returns:
        Хеш коммита HEAD или пустая строка если репозиторий не инициализирован
    """
    repo_path = get_module_resource_path(module_id)

    if not (repo_path / ".git").exists():
        return ""

    try:
        result = run(["git", "rev-parse", "HEAD"], cwd=repo_path, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except CalledProcessError:
        return ""


def get_module_commit_history(module_id: UUID) -> list[dict[str, str]]:
    """
    Получает историю коммитов для модуля.

    Использует --all чтобы отображать все коммиты, включая созданные
    в detached HEAD состоянии (не привязанные ни к одной ветке).

    Args:
        module_id: UUID модуля

    Returns:
        Список словарей с хешем, сообщением и датой

    Raises:
        CalledProcessError: Если git log не удался
    """
    repo_path = get_module_resource_path(module_id)

    try:
        result = run(
            ["git", "log", "--all", "--topo-order", "--pretty=format:%H|%s|%ai"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        history = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            commit_hash, message, date = line.split("|", 2)
            history.append({"hash": commit_hash, "message": message, "date": date})
        return history
    except CalledProcessError as e:
        raise CalledProcessError(e.returncode, e.cmd, e.output, e.stderr) from e


def get_module_git_tags(module_id: UUID) -> dict[str, list[str]]:
    """
    Возвращает словарь {commit_hash: [tag_name, ...]} для всех тегов репозитория.

    Args:
        module_id: UUID модуля

    Returns:
        Словарь commit_hash -> список тегов, указывающих на этот коммит.
        Пустой словарь, если репозиторий не инициализирован.
    """
    repo_path = get_module_resource_path(module_id)

    if not (repo_path / ".git").exists():
        return {}

    try:
        result = run(
            ["git", "tag", "-l", "--format=%(refname:short) %(objectname:short)"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        tags: dict[str, list[str]] = {}
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            tag_name, short_hash = parts[0], parts[1]
            # Resolve annotated tags to the tagged commit
            deref = run(
                ["git", "rev-list", "-n", "1", tag_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            full_hash = deref.stdout.strip() if deref.returncode == 0 else ""
            if not full_hash:
                continue
            tags.setdefault(full_hash, []).append(tag_name)
        return tags
    except CalledProcessError:
        return {}


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


class DirtyWorkingTreeError(Exception):
    """Рабочее дерево содержит незакоммиченные изменения."""


def _has_uncommitted_changes(repo_path: Path) -> bool:
    result = run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
    return bool(result.stdout.strip())


def _ensure_on_branch(repo_path: Path) -> None:
    """
    Если репозиторий в detached HEAD, переключается обратно на основную ветку.

    Если HEAD опережает ветку (есть коммиты, сделанные в detached HEAD состоянии),
    делает fast-forward ветки до HEAD перед переключением, чтобы эти коммиты
    не потерялись и были доступны через историю.
    """
    result = run(["git", "branch", "--show-current"], cwd=repo_path, capture_output=True, text=True)
    if result.stdout.strip():
        return

    branches_result = run(["git", "branch"], cwd=repo_path, capture_output=True, text=True)
    for branch in ("master", "main"):
        if branch not in branches_result.stdout:
            continue

        # Если ветка является предком HEAD — HEAD впереди, делаем fast-forward
        is_ancestor = run(
            ["git", "merge-base", "--is-ancestor", branch, "HEAD"],
            cwd=repo_path, capture_output=True, text=True
        )
        if is_ancestor.returncode == 0:
            head_hash = run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path, capture_output=True, text=True
            ).stdout.strip()
            run(["git", "branch", "-f", branch, head_hash], cwd=repo_path, capture_output=True, text=True)

        run(["git", "checkout", branch], cwd=repo_path, capture_output=True, text=True)
        return


def _ensure_release_unignored(repo_path: Path) -> None:
    """
    Добавляет исключения для release/ в .gitignore репозитория модуля,
    если их там ещё нет.
    """
    gitignore_path = repo_path / ".gitignore"
    if not gitignore_path.exists():
        return

    content = gitignore_path.read_text(encoding="utf-8")
    if "!release/" in content:
        return

    lines_to_add = "\n!release/\n!release/**\n"
    gitignore_path.write_text(content.rstrip() + lines_to_add, encoding="utf-8")


def release_commit_module(module_id: UUID, version_number: str, description: str) -> str:
    """
    Выполняет релизный коммит: копирует brep_files в release/brep_files,
    обновляет .gitignore, делает коммит и создаёт git-тег.

    Args:
        module_id: UUID модуля
        version_number: Номер версии (используется для тега)
        description: Описание (используется в сообщении коммита)

    Returns:
        Хеш коммита

    Raises:
        CalledProcessError: Если git-команды не удались
    """
    repo_path = get_module_resource_path(module_id)
    brep_src = get_module_brep_directory(module_id)
    release_brep_dst = repo_path / "release" / "brep_files"

    if not is_module_git_repo_initialized(module_id):
        init_module_git_repo(module_id)

    _ensure_on_branch(repo_path)
    _ensure_release_unignored(repo_path)

    release_brep_dst.mkdir(parents=True, exist_ok=True)
    if brep_src.exists():
        for src_file in brep_src.rglob("*"):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(brep_src)
            dst_file = release_brep_dst / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)

    try:
        run(["git", "add", ".gitignore", "release/"], cwd=repo_path, check=True, capture_output=True, text=True)

        status_result = run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
        commit_message = f"Release v{version_number}: {description}"

        if status_result.stdout.strip():
            run(["git", "commit", "-m", commit_message], cwd=repo_path, check=True, capture_output=True, text=True)

        tag_name = f"v{version_number}"
        existing_tags = run(["git", "tag", "-l", tag_name], cwd=repo_path, capture_output=True, text=True)
        if not existing_tags.stdout.strip():
            run(["git", "tag", "-a", tag_name, "-m", commit_message], cwd=repo_path, check=True, capture_output=True, text=True)

        hash_result = run(["git", "rev-parse", "HEAD"], cwd=repo_path, check=True, capture_output=True, text=True)
        return hash_result.stdout.strip()
    except CalledProcessError as e:
        raise CalledProcessError(e.returncode, e.cmd, e.output, e.stderr) from e


def checkout_module_commit(module_id: UUID, commit_hash: str, force: bool = False) -> None:
    """
    Переключает HEAD на указанный коммит (detached HEAD).

    Перед переключением возвращается на основную ветку чтобы не стаковать
    detached HEAD состояния. История всегда читается через _get_main_branch,
    поэтому все коммиты ветки видны вне зависимости от позиции HEAD.

    Args:
        module_id: UUID модуля
        commit_hash: Хеш коммита
        force: Если True — сбрасывает незакоммиченные изменения перед checkout

    Raises:
        DirtyWorkingTreeError: Если есть незакоммиченные изменения и force=False
        CalledProcessError: Если git команды не удались
        ValueError: Если commit_hash пустой или невалидный
    """
    if not commit_hash or not commit_hash.strip():
        raise ValueError("Commit hash cannot be empty")

    repo_path = get_module_resource_path(module_id)

    try:
        _ensure_on_branch(repo_path)

        if _has_uncommitted_changes(repo_path):
            if not force:
                raise DirtyWorkingTreeError("Есть незакоммиченные изменения")
            run(["git", "checkout", "--", "."], cwd=repo_path, check=True, capture_output=True, text=True)

        run(["git", "checkout", commit_hash], cwd=repo_path, check=True, capture_output=True, text=True)
    except DirtyWorkingTreeError:
        raise
    except CalledProcessError as e:
        raise CalledProcessError(e.returncode, e.cmd, e.output, e.stderr) from e