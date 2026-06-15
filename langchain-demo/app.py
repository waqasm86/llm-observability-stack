import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from langchain_ollama import ChatOllama
from langsmith import Client
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
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

HTTP_REQUESTS = Counter(
    "llm_observability_http_requests_total",
    "HTTP requests handled by the LLM observability API.",
    ["method", "route", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "llm_observability_http_request_duration_seconds",
    "End-to-end HTTP request latency.",
    ["method", "route"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300),
)
LLM_REQUESTS = Counter(
    "llm_observability_llm_requests_total",
    "Completed LLM requests.",
    ["model", "route", "outcome"],
)
LLM_ACTIVE_REQUESTS = Gauge(
    "llm_observability_llm_active_requests",
    "LLM requests currently being processed.",
    ["model", "route"],
)
LLM_REQUEST_DURATION = Histogram(
    "llm_observability_llm_request_duration_seconds",
    "End-to-end LLM request latency.",
    ["model", "route"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 20, 30, 60, 120, 300),
)
LLM_TTFT = Histogram(
    "llm_observability_time_to_first_token_seconds",
    "Time from proxy request start to the first streamed response bytes.",
    ["model", "route"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 20, 30, 60),
)
LLM_ITL = Histogram(
    "llm_observability_inter_token_latency_seconds",
    "Average inter-token latency derived from Ollama evaluation duration and token count.",
    ["model", "route"],
    buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5),
)
LLM_PROMPT_TOKENS = Counter(
    "llm_observability_prompt_tokens_total",
    "Prompt tokens reported by the inference backend.",
    ["model", "route"],
)
LLM_GENERATED_TOKENS = Counter(
    "llm_observability_generated_tokens_total",
    "Generated tokens reported by the inference backend.",
    ["model", "route"],
)
LLM_TOKEN_THROUGHPUT = Histogram(
    "llm_observability_generated_tokens_per_second",
    "Generated token throughput reported by Ollama.",
    ["model", "route"],
    buckets=(0.5, 1, 2, 5, 10, 20, 40, 80, 160, 320),
)


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


def get_model_name(payload: Optional[Any] = None) -> str:
    if isinstance(payload, dict) and payload.get("model"):
        return str(payload["model"])
    return get_env("OLLAMA_MODEL", DEFAULT_MODEL)


def observe_ollama_payload(payload: Optional[Any], model: str, route: str) -> None:
    if not isinstance(payload, dict):
        return

    prompt_tokens = payload.get("prompt_eval_count")
    generated_tokens = payload.get("eval_count")
    eval_duration_ns = payload.get("eval_duration")

    if isinstance(prompt_tokens, (int, float)) and prompt_tokens >= 0:
        LLM_PROMPT_TOKENS.labels(model=model, route=route).inc(float(prompt_tokens))
    if isinstance(generated_tokens, (int, float)) and generated_tokens >= 0:
        LLM_GENERATED_TOKENS.labels(model=model, route=route).inc(float(generated_tokens))
    if (
        isinstance(generated_tokens, (int, float))
        and isinstance(eval_duration_ns, (int, float))
        and generated_tokens >= 0
        and eval_duration_ns > 0
    ):
        tokens_per_second = float(generated_tokens) / (float(eval_duration_ns) / 1_000_000_000)
        LLM_TOKEN_THROUGHPUT.labels(model=model, route=route).observe(tokens_per_second)
        LLM_ITL.labels(model=model, route=route).observe(1.0 / tokens_per_second)


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


@app.middleware("http")
async def observe_http_request(request: Request, call_next):  # type: ignore[no-untyped-def]
    if request.url.path == "/metrics":
        return await call_next(request)

    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        route = getattr(request.scope.get("route"), "path", request.url.path)
        HTTP_REQUESTS.labels(
            method=request.method,
            route=route,
            status=str(status_code),
        ).inc()
        HTTP_REQUEST_DURATION.labels(method=request.method, route=route).observe(
            time.perf_counter() - started
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


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


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
    model = get_model_name()
    route = "invoke"
    started = time.perf_counter()
    LLM_ACTIVE_REQUESTS.labels(model=model, route=route).inc()
    try:
        llm = get_llm()
        prompt = req.prompt if not req.system else f"System: {req.system}\n\nUser: {req.prompt}"
        response = llm.invoke(prompt)
        content = getattr(response, "content", response)
        response_metadata = getattr(response, "response_metadata", None)
        observe_ollama_payload(response_metadata, model, route)
        LLM_REQUESTS.labels(model=model, route=route, outcome="success").inc()
        return InvokeOut(
            response=str(content),
            model=model,
            ollama_base_url=get_env("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
        )
    except Exception as exc:  # pragma: no cover - runtime surface for demo support drills
        LLM_REQUESTS.labels(model=model, route=route, outcome="error").inc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        LLM_ACTIVE_REQUESTS.labels(model=model, route=route).dec()
        LLM_REQUEST_DURATION.labels(model=model, route=route).observe(time.perf_counter() - started)


@app.api_route("/ollama/{upstream_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def ollama_proxy(upstream_path: str, request: Request):
    upstream_base_url = get_ollama_upstream_base_url()
    normalized_path = f"/{upstream_path.lstrip('/')}"
    upstream_url = f"{upstream_base_url}{normalized_path}"
    if request.url.query:
        upstream_url = f"{upstream_url}?{request.url.query}"

    request_body = await request.body()
    body_json = safe_json(request_body)
    model = get_model_name(body_json)
    route = "ollama_proxy"
    started = time.perf_counter()
    stream_owns_metrics = False
    LLM_ACTIVE_REQUESTS.labels(model=model, route=route).inc()
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
                stream_buffer = b""
                final_payload: Optional[Any] = None
                first_chunk_at: Optional[float] = None
                try:
                    async for chunk in upstream_response.aiter_bytes(chunk_size=8192):
                        if not chunk:
                            continue
                        now = time.perf_counter()
                        if first_chunk_at is None:
                            first_chunk_at = now
                            LLM_TTFT.labels(model=model, route=route).observe(now - started)
                        stream_buffer += chunk
                        lines = stream_buffer.split(b"\n")
                        stream_buffer = lines.pop()
                        for line in lines:
                            parsed = safe_json(line.strip())
                            if isinstance(parsed, dict) and parsed.get("done") is True:
                                final_payload = parsed
                        if preview_chars < TRACE_PREVIEW_LIMIT:
                            decoded = chunk.decode("utf-8", errors="ignore")
                            remaining = TRACE_PREVIEW_LIMIT - preview_chars
                            sample = decoded[:remaining]
                            preview_parts.append(sample)
                            preview_chars += len(sample)
                        yield chunk
                    if stream_buffer.strip():
                        parsed = safe_json(stream_buffer.strip())
                        if isinstance(parsed, dict) and parsed.get("done") is True:
                            final_payload = parsed
                    observe_ollama_payload(final_payload, model, route)
                    outcome = "success" if upstream_status_code < 500 else "error"
                    LLM_REQUESTS.labels(model=model, route=route, outcome=outcome).inc()
                    finish_proxy_trace(
                        client,
                        run_id,
                        upstream_status_code,
                        outputs={"streamed": True, "response_preview": "".join(preview_parts)},
                    )
                except Exception as exc:
                    LLM_REQUESTS.labels(model=model, route=route, outcome="error").inc()
                    finish_proxy_trace(
                        client,
                        run_id,
                        upstream_status_code,
                        outputs={"streamed": True},
                        error=str(exc),
                    )
                    raise
                finally:
                    LLM_ACTIVE_REQUESTS.labels(model=model, route=route).dec()
                    LLM_REQUEST_DURATION.labels(model=model, route=route).observe(
                        time.perf_counter() - started
                    )
                    await upstream_response.aclose()
                    await async_client.aclose()

            stream_owns_metrics = True
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
        response_payload = safe_json(upstream_response.content)
        observe_ollama_payload(response_payload, model, route)
        outcome = "success" if upstream_response.status_code < 500 else "error"
        LLM_REQUESTS.labels(model=model, route=route, outcome=outcome).inc()
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type"),
        )
    except httpx.HTTPError as exc:
        LLM_REQUESTS.labels(model=model, route=route, outcome="error").inc()
        finish_proxy_trace(client, run_id, None, error=str(exc))
        raise HTTPException(status_code=502, detail=f"Ollama proxy request failed: {exc}") from exc
    finally:
        if not stream_owns_metrics:
            LLM_ACTIVE_REQUESTS.labels(model=model, route=route).dec()
            LLM_REQUEST_DURATION.labels(model=model, route=route).observe(time.perf_counter() - started)
