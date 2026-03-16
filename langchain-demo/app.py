import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama

APP_TITLE = "k3s-ollama-langsmith-demo"
DEFAULT_MODEL = "gemma3-1b-it-gguf-local"
DEFAULT_BASE_URL = "http://ollama:11434"
DEFAULT_TEMPERATURE = 0.2

app = FastAPI(title=APP_TITLE)


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
    }


@app.get("/healthz")
def healthz() -> dict:
    return {
        "status": "ok",
        "model": get_env("OLLAMA_MODEL", DEFAULT_MODEL),
        "ollama_base_url": get_env("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
        "langsmith_tracing": get_env("LANGSMITH_TRACING", "false"),
        "langsmith_project": os.environ.get("LANGSMITH_PROJECT"),
        "etcd_endpoints": os.environ.get("ETCD_ENDPOINTS"),
    }


@app.get("/config")
def config() -> dict:
    return {
        "model": get_env("OLLAMA_MODEL", DEFAULT_MODEL),
        "ollama_base_url": get_env("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
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
