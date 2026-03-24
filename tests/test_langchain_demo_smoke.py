from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = REPO_ROOT / "langchain-demo" / "app.py"

_SPEC = importlib.util.spec_from_file_location("langchain_demo_app", APP_PATH)
assert _SPEC is not None and _SPEC.loader is not None
app_module = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(app_module)


@pytest.fixture(autouse=True)
def reset_env_and_state(monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep each test deterministic and independent from host environment.
    for name in [
        "OLLAMA_BASE_URL",
        "OLLAMA_UPSTREAM_BASE_URL",
        "OLLAMA_MODEL",
        "OLLAMA_TEMPERATURE",
        "OLLAMA_PROXY_TRACE_LANGSMITH",
        "OLLAMA_PROXY_TIMEOUT_SECONDS",
        "LANGSMITH_API_KEY",
        "LANGCHAIN_API_KEY",
        "LANGSMITH_ENDPOINT",
        "LANGCHAIN_ENDPOINT",
        "LANGSMITH_PROJECT",
        "LANGCHAIN_PROJECT",
    ]:
        monkeypatch.delenv(name, raising=False)

    app_module._LANGSMITH_CLIENT = None
    app_module._LANGSMITH_CLIENT_UNAVAILABLE = False


def test_root_and_healthz_endpoints() -> None:
    with TestClient(app_module.app) as client:
        root_resp = client.get("/")
        assert root_resp.status_code == 200
        payload = root_resp.json()
        assert payload["invoke"] == "/invoke"
        assert payload["health"] == "/healthz"
        assert payload["ollama_proxy"] == "/ollama/api/*"

        health_resp = client.get("/healthz")
        assert health_resp.status_code == 200
        health = health_resp.json()
        assert health["status"] == "ok"
        assert health["ollama_base_url"] == "http://ollama:11434"
        assert health["ollama_upstream_base_url"] == "http://ollama:11434"


def test_invoke_success_and_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeLLM:
        def invoke(self, prompt: str) -> SimpleNamespace:
            assert "User: hello from test" in prompt
            return SimpleNamespace(content="synthetic-response")

    with TestClient(app_module.app) as client:
        monkeypatch.setattr(app_module, "get_llm", lambda: FakeLLM())
        ok_resp = client.post("/invoke", json={"prompt": "hello from test", "system": "be brief"})
        assert ok_resp.status_code == 200
        assert ok_resp.json()["response"] == "synthetic-response"

        def raising_llm() -> FakeLLM:
            raise RuntimeError("llm unavailable")

        monkeypatch.setattr(app_module, "get_llm", raising_llm)
        err_resp = client.post("/invoke", json={"prompt": "hello from test"})
        assert err_resp.status_code == 500
        assert "llm unavailable" in err_resp.text


def test_ollama_proxy_forwards_non_streaming_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        status_code = 200
        headers = {"content-type": "application/json"}
        content = b'{"ok":true}'
        text = '{"ok":true}'

        @staticmethod
        def json() -> dict[str, bool]:
            return {"ok": True}

    class FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            captured["client_init"] = kwargs

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
            return None

        async def request(self, **kwargs: object) -> FakeResponse:
            captured.update(kwargs)
            return FakeResponse()

    monkeypatch.setenv("OLLAMA_UPSTREAM_BASE_URL", "http://ollama:11434")
    monkeypatch.setattr(app_module.httpx, "AsyncClient", FakeAsyncClient)

    with TestClient(app_module.app) as client:
        resp = client.post(
            "/ollama/api/chat?trace_id=abc",
            json={"stream": False, "messages": [{"role": "user", "content": "hello"}]},
            headers={"x-test-header": "smoke"},
        )

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert captured["url"] == "http://ollama:11434/api/chat?trace_id=abc"
    assert captured["method"] == "POST"
    client_init = captured["client_init"]
    assert isinstance(client_init, dict)
    assert "timeout" in client_init
    assert isinstance(captured["content"], (bytes, bytearray))
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert "host" not in {k.lower() for k in headers.keys()}


def test_ollama_proxy_forwards_streaming_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeStreamResponse:
        status_code = 200
        headers = {"content-type": "application/x-ndjson"}

        async def aiter_bytes(self, chunk_size: int = 8192):  # type: ignore[no-untyped-def]
            _ = chunk_size
            for chunk in [b'{"token":"hello"}\n', b'{"token":"world"}\n']:
                yield chunk

        async def aclose(self) -> None:
            captured["response_closed"] = True

    class FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            captured["client_init"] = kwargs

        def build_request(self, **kwargs: object) -> dict[str, object]:
            captured["build_request"] = kwargs
            return {"built": True, **kwargs}

        async def send(self, request: object, stream: bool = False) -> FakeStreamResponse:
            captured["send_request"] = request
            captured["send_stream"] = stream
            return FakeStreamResponse()

        async def aclose(self) -> None:
            captured["client_closed"] = True

    monkeypatch.setenv("OLLAMA_UPSTREAM_BASE_URL", "http://ollama:11434")
    monkeypatch.setattr(app_module.httpx, "AsyncClient", FakeAsyncClient)

    with TestClient(app_module.app) as client:
        resp = client.post(
            "/ollama/api/chat",
            json={"stream": True, "messages": [{"role": "user", "content": "hello"}]},
        )

    assert resp.status_code == 200
    assert resp.content == b'{"token":"hello"}\n{"token":"world"}\n'
    assert captured["send_stream"] is True
    assert captured["response_closed"] is True
    assert captured["client_closed"] is True


def test_ollama_proxy_surfaces_upstream_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingAsyncClient:
        async def __aenter__(self) -> "FailingAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
            return None

        async def request(self, **_: object) -> object:
            raise app_module.httpx.RequestError(
                "network-failure",
                request=app_module.httpx.Request("POST", "http://ollama:11434/api/chat"),
            )

    monkeypatch.setattr(app_module.httpx, "AsyncClient", lambda *args, **kwargs: FailingAsyncClient())

    with TestClient(app_module.app) as client:
        resp = client.post("/ollama/api/chat", json={"stream": False})

    assert resp.status_code == 502
    assert "network-failure" in resp.text
