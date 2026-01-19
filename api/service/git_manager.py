from subprocess import run, CalledProcessError
from pathlib import Path
from uuid import UUID


def init_module_git_repo(module_id: UUID) -> str:
    """
    Инициализирует Git репозиторий для модуля.
    
    Args:
        module_id: UUID модуля
        
    Returns:
        Путь к репозиторию
        
    Raises:
        CalledProcessError: Если git init не удался
    """
    repo_path = Path("api/resources/brep_files") / str(module_id)
    
    try:
        run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
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
    repo_path = Path("api/resources/brep_files") / str(module_id)
    
    try:
        # git add .
        run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
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
    repo_path = Path("api/resources/brep_files") / str(module_id)
    
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