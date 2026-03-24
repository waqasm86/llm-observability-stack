import json
import os
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from langchain_ollama import ChatOllama
from langsmith import Client
from pydantic import BaseModel, Field

APP_TITLE = "k3s-ollama-langsmith-demo"
DEFAULT_MODEL = "gemma3-1b-it-gguf-local"
DEFAULT_BASE_URL = "http://ollama:11434"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_PROXY_PATH_PREFIX = "/ollama"
DEFAULT_PROXY_TIMEOUT_SECONDS = 180.0
TRACE_PREVIEW_LIMIT = 8000

app = FastAPI(title=APP_TITLE)
_LANGSMITH_CLIENT: Optional[Client] = None
_LANGSMITH_CLIENT_UNAVAILABLE = False


class PromptIn(BaseModel):
    prompt: str = Field(..., min_length=1)
    system: Optional[str] = None


class InvokeOut(BaseModel):
    response: str
    model: str
    ollama_base_url: str


def get_env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def get_env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_proxy_timeout_seconds() -> float:
    try:
        return float(get_env("OLLAMA_PROXY_TIMEOUT_SECONDS", str(DEFAULT_PROXY_TIMEOUT_SECONDS)))
    except ValueError:
        return DEFAULT_PROXY_TIMEOUT_SECONDS


def get_ollama_upstream_base_url() -> str:
    return get_env("OLLAMA_UPSTREAM_BASE_URL", get_env("OLLAMA_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")


def safe_json(value: bytes) -> Optional[Any]:
    if not value:
        return None
    try:
        return json.loads(value.decode("utf-8"))
    except Exception:
        return None


def truncate_text(value: str, limit: int = TRACE_PREVIEW_LIMIT) -> str:
    if len(value) <= limit:
        return value
    return value[:limit]


def get_langsmith_client() -> Optional[Client]:
    global _LANGSMITH_CLIENT, _LANGSMITH_CLIENT_UNAVAILABLE
    if _LANGSMITH_CLIENT_UNAVAILABLE:
        return None
    if _LANGSMITH_CLIENT is not None:
        return _LANGSMITH_CLIENT

    api_key = os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")
    if not api_key:
        _LANGSMITH_CLIENT_UNAVAILABLE = True
        return None

    try:
        kwargs: dict[str, Any] = {"api_key": api_key}
        endpoint = os.environ.get("LANGSMITH_ENDPOINT") or os.environ.get("LANGCHAIN_ENDPOINT")
        if endpoint:
            kwargs["api_url"] = endpoint
        _LANGSMITH_CLIENT = Client(**kwargs)
        return _LANGSMITH_CLIENT
    except Exception:
        _LANGSMITH_CLIENT_UNAVAILABLE = True
        return None


def get_langsmith_project_name() -> str:
    return os.environ.get("LANGSMITH_PROJECT") or os.environ.get("LANGCHAIN_PROJECT") or "default"


def start_proxy_trace(
    method: str, upstream_path: str, query: str, payload: Optional[Any]
) -> tuple[Optional[Client], Optional[UUID]]:
    if not get_env_bool("OLLAMA_PROXY_TRACE_LANGSMITH", True):
        return None, None

    client = get_langsmith_client()
    if client is None:
        return None, None

    run_id = uuid4()
    inputs: dict[str, Any] = {"method": method, "upstream_path": upstream_path}
    if query:
        inputs["query"] = query
    if payload is not None:
        inputs["payload"] = payload

    try:
        client.create_run(
            name=f"open_webui_ollama_proxy:{method.lower()}:{upstream_path}",
            run_type="llm",
            project_name=get_langsmith_project_name(),
            id=run_id,
            start_time=datetime.now(timezone.utc),
            inputs=inputs,
            tags=["open-webui", "ollama-proxy"],
        )
        return client, run_id
    except Exception:
        return None, None


def finish_proxy_trace(
    client: Optional[Client],
    run_id: Optional[UUID],
    status_code: Optional[int],
    outputs: Optional[dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    if client is None or run_id is None:
        return

    update_outputs = dict(outputs or {})
    if status_code is not None:
        update_outputs.setdefault("status_code", status_code)

    try:
        client.update_run(
            run_id=run_id,
            end_time=datetime.now(timezone.utc),
            outputs=update_outputs if update_outputs else None,
            error=error,
        )
    except Exception:
        return


def extract_response_payload(resp: Any) -> dict[str, Any]:
    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return {"response_json": resp.json()}
        except Exception:
            pass
    return {"response_text_preview": truncate_text(resp.text)}


def build_upstream_headers(request: Request) -> dict[str, str]:
    forwarded: dict[str, str] = {}
    skip_headers = {"host", "content-length", "connection"}
    for key, value in request.headers.items():
        if key.lower() in skip_headers:
            continue
        forwarded[key] = value
    return forwarded


def get_llm() -> ChatOllama:
    return ChatOllama(
        model=get_env("OLLAMA_MODEL", DEFAULT_MODEL),
        base_url=get_env("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
        temperature=float(get_env("OLLAMA_TEMPERATURE", str(DEFAULT_TEMPERATURE))),
    )


@app.get("/")
def root() -> dict:
    return {
        "name": APP_TITLE,
        "health": "/healthz",
        "invoke": "/invoke",
        "config": "/config",
        "ollama_proxy": f"{get_env('OLLAMA_PROXY_PATH_PREFIX', DEFAULT_PROXY_PATH_PREFIX)}/api/*",
    }


@app.get("/healthz")
def healthz() -> dict:
    return {
        "status": "ok",
        "model": get_env("OLLAMA_MODEL", DEFAULT_MODEL),
        "ollama_base_url": get_env("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
        "ollama_upstream_base_url": get_ollama_upstream_base_url(),
        "langsmith_tracing": get_env("LANGSMITH_TRACING", "false"),
        "langsmith_project": os.environ.get("LANGSMITH_PROJECT"),
        "etcd_endpoints": os.environ.get("ETCD_ENDPOINTS"),
    }


@app.get("/config")
def config() -> dict:
    return {
        "model": get_env("OLLAMA_MODEL", DEFAULT_MODEL),
        "ollama_base_url": get_env("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
        "ollama_upstream_base_url": get_ollama_upstream_base_url(),
        "temperature": float(get_env("OLLAMA_TEMPERATURE", str(DEFAULT_TEMPERATURE))),
        "langsmith_project": os.environ.get("LANGSMITH_PROJECT"),
        "langsmith_endpoint": os.environ.get("LANGSMITH_ENDPOINT"),
        "etcd_endpoints": os.environ.get("ETCD_ENDPOINTS"),
    }


@app.post("/invoke", response_model=InvokeOut)
def invoke(req: PromptIn) -> InvokeOut:
    try:
        llm = get_llm()
        prompt = req.prompt if not req.system else f"System: {req.system}\n\nUser: {req.prompt}"
        response = llm.invoke(prompt)
        content = getattr(response, "content", response)
        return InvokeOut(
            response=str(content),
            model=get_env("OLLAMA_MODEL", DEFAULT_MODEL),
            ollama_base_url=get_env("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
        )
    except Exception as exc:  # pragma: no cover - runtime surface for demo support drills
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.api_route("/ollama/{upstream_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def ollama_proxy(upstream_path: str, request: Request):
    upstream_base_url = get_ollama_upstream_base_url()
    normalized_path = f"/{upstream_path.lstrip('/')}"
    upstream_url = f"{upstream_base_url}{normalized_path}"
    if request.url.query:
        upstream_url = f"{upstream_url}?{request.url.query}"

    request_body = await request.body()
    body_json = safe_json(request_body)
    proxy_headers = build_upstream_headers(request)

    client, run_id = start_proxy_trace(
        method=request.method,
        upstream_path=normalized_path,
        query=request.url.query,
        payload=body_json,
    )

    stream_requested = bool(isinstance(body_json, dict) and body_json.get("stream") is True)
    timeout_seconds = get_proxy_timeout_seconds()
    timeout = httpx.Timeout(timeout_seconds, connect=10.0)

    try:
        if stream_requested:
            async_client = httpx.AsyncClient(timeout=timeout)
            upstream_request = async_client.build_request(
                method=request.method,
                url=upstream_url,
                headers=proxy_headers,
                content=request_body or None,
            )
            try:
                upstream_response = await async_client.send(upstream_request, stream=True)
            except httpx.HTTPError:
                await async_client.aclose()
                raise
            content_type = upstream_response.headers.get("content-type", "application/octet-stream")
            upstream_status_code = upstream_response.status_code

            async def iter_stream():
                preview_parts: list[str] = []
                preview_chars = 0
                try:
                    async for chunk in upstream_response.aiter_bytes(chunk_size=8192):
                        if not chunk:
                            continue
                        if preview_chars < TRACE_PREVIEW_LIMIT:
                            decoded = chunk.decode("utf-8", errors="ignore")
                            remaining = TRACE_PREVIEW_LIMIT - preview_chars
                            sample = decoded[:remaining]
                            preview_parts.append(sample)
                            preview_chars += len(sample)
                        yield chunk
                    finish_proxy_trace(
                        client,
                        run_id,
                        upstream_status_code,
                        outputs={"streamed": True, "response_preview": "".join(preview_parts)},
                    )
                except Exception as exc:
                    finish_proxy_trace(
                        client,
                        run_id,
                        upstream_status_code,
                        outputs={"streamed": True},
                        error=str(exc),
                    )
                    raise
                finally:
                    await upstream_response.aclose()
                    await async_client.aclose()

            return StreamingResponse(
                iter_stream(),
                media_type=content_type,
                status_code=upstream_status_code,
            )

        async with httpx.AsyncClient(timeout=timeout) as async_client:
            upstream_response = await async_client.request(
                method=request.method,
                url=upstream_url,
                headers=proxy_headers,
                content=request_body or None,
            )

        finish_proxy_trace(
            client,
            run_id,
            upstream_response.status_code,
            outputs=extract_response_payload(upstream_response),
        )
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type"),
        )
    except httpx.HTTPError as exc:
        finish_proxy_trace(client, run_id, None, error=str(exc))
        raise HTTPException(status_code=502, detail=f"Ollama proxy request failed: {exc}") from exc
