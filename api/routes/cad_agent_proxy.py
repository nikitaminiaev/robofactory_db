import json
import os
import urllib.error
import urllib.request
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter()


class CadAgentExecuteRequest(BaseModel):
    message: Optional[str] = None
    scad_filename: Optional[str] = None
    scad_content: Optional[str] = None
    stl_filename: Optional[str] = None
    render_stl: bool = True
    git_args: Optional[list[str]] = None
    prompt: Optional[str] = None


def _cad_agent_base_url() -> str:
    return os.getenv("CAD_AGENT_URL", "http://cad-agent:8010").rstrip("/")


@router.get("/cad-agent/health")
async def cad_agent_health():
    upstream_url = f"{_cad_agent_base_url()}/health"
    upstream_request = urllib.request.Request(upstream_url, method="GET")
    try:
        with urllib.request.urlopen(upstream_request, timeout=3) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except (urllib.error.URLError, urllib.error.HTTPError):
        raise HTTPException(status_code=503, detail="CAD agent недоступен")


@router.get("/modules/{module_id}/cad-agent/has-scad")
async def has_scad_file(module_id: str):
    try:
        module_uuid = UUID(module_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный module_id") from exc

    upstream_url = f"{_cad_agent_base_url()}/internal/modules/{module_uuid}/has-scad"
    token = os.getenv("CAD_AGENT_TOKEN", "").strip()
    headers = {}
    if token:
        headers["X-Cad-Agent-Token"] = token

    upstream_request = urllib.request.Request(upstream_url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(upstream_request, timeout=10) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        detail = body or "CAD agent error"
        raise HTTPException(status_code=exc.code, detail=detail) from exc
    except urllib.error.URLError as exc:
        raise HTTPException(status_code=503, detail=f"CAD agent недоступен: {exc.reason}") from exc


@router.post("/modules/{module_id}/cad-agent/execute")
async def execute_cad_agent(module_id: str, request: CadAgentExecuteRequest):
    try:
        module_uuid = UUID(module_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный module_id") from exc

    payload = request.model_dump(exclude_none=True)
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

    try:
        with urllib.request.urlopen(upstream_request, timeout=180) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        if body:
            try:
                parsed = json.loads(body)
                detail = parsed.get("detail", body)
            except json.JSONDecodeError:
                detail = body
        else:
            detail = "CAD agent error"
        raise HTTPException(status_code=exc.code, detail=detail) from exc
    except urllib.error.URLError as exc:
        raise HTTPException(status_code=503, detail=f"CAD agent недоступен: {exc.reason}") from exc
