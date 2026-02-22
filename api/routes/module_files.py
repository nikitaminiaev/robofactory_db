import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from service.constants import get_module_resource_path, get_module_stl_directory
from service.git_manager import commit_module_changes, get_module_git_diff

router = APIRouter()


class ScadFileDTO(BaseModel):
    filename: str
    content: str


class GitCommitRequest(BaseModel):
    message: str


def _cad_agent_base_url() -> str:
    return os.getenv("CAD_AGENT_URL", "http://cad-agent:8010").rstrip("/")


def _call_cad_agent_render(module_uuid: UUID, scad_filename: str) -> dict:
    payload = {"render_stl": True, "scad_filename": scad_filename}
    upstream_url = f"{_cad_agent_base_url()}/internal/modules/{module_uuid}/execute"
    token = os.getenv("CAD_AGENT_TOKEN", "").strip()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Cad-Agent-Token"] = token

    request_data = json.dumps(payload).encode("utf-8")
    upstream_request = urllib.request.Request(
        upstream_url,
        data=request_data,
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(upstream_request, timeout=180) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


@router.get("/modules/{module_id}/scad-files", response_model=List[ScadFileDTO])
async def get_scad_files(module_id: str):
    try:
        module_uuid = UUID(module_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный module_id") from exc

    repo_path = get_module_resource_path(module_uuid)
    if not repo_path.exists():
        return []

    result = []
    for scad_file in sorted(repo_path.glob("*.scad")):
        try:
            content = scad_file.read_text(encoding="utf-8")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Ошибка чтения файла {scad_file.name}: {exc}") from exc
        result.append(ScadFileDTO(filename=scad_file.name, content=content))

    return result


class SaveScadRequest(BaseModel):
    content: str


class SaveScadResponse(BaseModel):
    saved: bool
    rendered: bool
    stl_filename: Optional[str] = None
    render_error: Optional[str] = None


@router.put("/modules/{module_id}/scad-files/{filename}")
async def save_scad_file(module_id: str, filename: str, request: SaveScadRequest) -> SaveScadResponse:
    try:
        module_uuid = UUID(module_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный module_id") from exc

    if not filename.endswith(".scad"):
        raise HTTPException(status_code=400, detail="Разрешены только .scad файлы")

    safe_name = Path(filename).name
    repo_path = get_module_resource_path(module_uuid)
    repo_path.mkdir(parents=True, exist_ok=True)

    target = repo_path / safe_name
    try:
        target.write_text(request.content, encoding="utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ошибка записи файла: {exc}") from exc

    stl_filename = None
    render_error = None
    rendered = False

    try:
        render_result = _call_cad_agent_render(module_uuid, safe_name)
        stl_path = render_result.get("stl_path", "")
        if stl_path:
            stl_filename = Path(stl_path).name
        rendered = True
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        render_error = body or f"CAD agent вернул ошибку {exc.code}"
    except urllib.error.URLError as exc:
        render_error = f"CAD agent недоступен: {exc.reason}"
    except Exception as exc:
        render_error = str(exc)

    return SaveScadResponse(
        saved=True,
        rendered=rendered,
        stl_filename=stl_filename,
        render_error=render_error,
    )


@router.get("/modules/{module_id}/stl-file/{filename}")
async def get_stl_file(module_id: str, filename: str):
    try:
        module_uuid = UUID(module_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный module_id") from exc

    safe_name = Path(filename).name
    stl_dir = get_module_stl_directory(module_uuid)
    stl_path = stl_dir / safe_name

    if not stl_path.exists():
        raise HTTPException(status_code=404, detail=f"STL файл не найден: {safe_name}")

    return FileResponse(
        path=str(stl_path),
        media_type="model/stl",
        filename=safe_name,
    )


@router.get("/modules/{module_id}/stl-files")
async def list_stl_files(module_id: str):
    try:
        module_uuid = UUID(module_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный module_id") from exc

    stl_dir = get_module_stl_directory(module_uuid)
    if not stl_dir.exists():
        return []

    return [f.name for f in sorted(stl_dir.glob("*.stl"))]


@router.get("/modules/{module_id}/git-diff")
async def get_git_diff(module_id: str):
    try:
        module_uuid = UUID(module_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный module_id") from exc

    diff = get_module_git_diff(module_uuid)
    return {"diff": diff}


@router.post("/modules/{module_id}/git-commit")
async def git_commit(module_id: str, request: GitCommitRequest):
    try:
        module_uuid = UUID(module_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный module_id") from exc

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Сообщение коммита не может быть пустым")

    try:
        commit_hash = commit_module_changes(module_uuid, request.message.strip())
        return {"commit_hash": commit_hash}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ошибка коммита: {exc}") from exc
