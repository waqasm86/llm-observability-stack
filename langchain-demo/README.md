# langchain-demo

`langchain-demo` is the local FastAPI application that provides:

- a simple `/invoke` API for prompt testing
- health/config endpoints for notebook and cluster checks
- an Ollama-compatible proxy path at `/ollama/*`
- optional LangSmith tracing for proxied Open WebUI traffic

## Why It Exists

This service is the observability bridge in the stack. Instead of sending browser traffic directly from Open WebUI to Ollama, Open WebUI can send Ollama-compatible requests through this service so the project can:

- inspect proxy health independently
- keep a stable API surface for notebooks and smoke tests
- emit LangSmith traces for local demo traffic

## Source Files

- `app.py` - FastAPI app and traced proxy logic
- `requirements.txt` - Python dependencies
- `Dockerfile` - local image build input

## Main Endpoints

- `GET /`
- `GET /healthz`
- `GET /config`
- `POST /invoke`
- `ANY /ollama/{path}` for upstream Ollama proxying

## Important Environment Variables

- `OLLAMA_MODEL`
- `OLLAMA_BASE_URL`
- `OLLAMA_UPSTREAM_BASE_URL`
- `OLLAMA_TEMPERATURE`
- `OLLAMA_PROXY_TIMEOUT_SECONDS`
- `OLLAMA_PROXY_TRACE_LANGSMITH`
- `LANGSMITH_API_KEY` or `LANGCHAIN_API_KEY`
- `LANGSMITH_ENDPOINT` / `LANGCHAIN_ENDPOINT`
- `LANGSMITH_PROJECT` / `LANGCHAIN_PROJECT`

## Local Image Workflow

Build:

```bash
../hack/build-local-image.sh langchain-demo 0.1.1 ./langchain-demo
```

Import into k3s:

```bash
../hack/import-local-image-to-k3s.sh langchain-demo 0.1.1
```

Restart deployment:

```bash
kubectl rollout restart deploy/langchain-demo -n llm-observability
kubectl rollout status deploy/langchain-demo -n llm-observability
```

## Useful Checks

Port-forward:

```bash
kubectl port-forward -n llm-observability svc/langchain-demo 8000:8000
```

Health:

```bash
curl -s http://localhost:8000/healthz | jq
curl -s http://localhost:8000/config | jq
```

Invoke:

```bash
curl -s http://localhost:8000/invoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Explain Kubernetes rollout strategy in three lines."}' | jq
```

Proxy to Ollama:

```bash
curl -s http://localhost:8000/ollama/api/tags | jq
```

## Operational Notes

- This service is intended to run from a prebuilt local image, not from mutable runtime installs.
- If notebook cells fail on `localhost:8000`, verify the port-forward first.
- If LangSmith metrics are missing, the proxy still works, but tracing fields may remain empty until credentials are fixed.
