# llm-observability-stack

Umbrella Helm chart for a local single-node stack:

- `k3s`
- NVIDIA GPU runtime + device plugin (installed separately)
- `ollama`
- `open-webui`
- `langchain` demo API with `langsmith` tracing

This repository is tuned for local Xubuntu/k3s workflows and GGUF models mounted from host storage.

GitHub repository: https://github.com/waqasm86/llm-observability-stack

## Project documentation

- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)
- Support guide: [SUPPORT.md](SUPPORT.md)
- Code of conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Publishing notes: [docs/GITHUB-PUBLISHING.md](docs/GITHUB-PUBLISHING.md)

## What this deploys

- Vendored `ollama` chart (`charts/ollama`)
- Vendored `open-webui` chart (`charts/open-webui`)
- Local Modelfile ConfigMap for GGUF-backed Ollama model creation
- LangChain demo API deployment/service (observability test endpoint)
- Optional secret creation for LangSmith and Open WebUI
- Optional `etcd` only when you explicitly enable a backing-store troubleshooting scenario

## Why this version is better

This revision removes the weakest part of the old setup: runtime `pip install` inside the `langchain-demo` pod.

The demo app is now intended to run from a prebuilt local image:

- faster startup
- repeatable pod behavior
- less dependence on internet/package index availability
- stronger support-engineering story

The chart also now:

- pins `ollama` and `open-webui` image tags
- keeps `etcd` disabled by default unless you are actively testing it
- includes a GitHub Actions workflow for `helm lint` and `helm template`

## Prerequisites

- Kubernetes: `k3s` (single node is supported)
- NVIDIA stack: container toolkit + working GPU runtime + NVIDIA device plugin in cluster
- `helm` and `kubectl` installed on host
- Docker installed on host to build/import the local `langchain-demo` image
- Local GGUF model file available on host filesystem

## Quick start

Use the example values file as your starting point:

```bash
cp values.local-k3s.example.yaml values.local-k3s.yaml
```

Edit `values.local-k3s.yaml` and set:

- `ollamaModel.gguf.hostPath` to your GGUF parent directory
- `ollama.volumes[0].hostPath.path` to the same directory
- LangSmith credentials (or existing secret reference)
- Open WebUI secret key (32+ chars)

Current local runtime profile in this repository:

- `open-webui` is exposed on `LoadBalancer` (`localhost:8080`)
- `ollama` and `langchain-demo` are internal `ClusterIP` services
- `pythonToolbox.enabled: false`
- `langsmithDashboardSeeder.enabled: false`
- LangSmith traces are generated on-demand from Open WebUI traffic via `langchain-demo` proxy

### Values file strategy

- `values.yaml`: git-tracked defaults, no secrets.
- `values.local-k3s.yaml`: local machine overrides + secrets (gitignored).
- `values.local-k3s.example.yaml`: safe template for onboarding and CI render checks.

### Build the local LangChain demo image

```bash
./hack/build-local-image.sh langchain-demo 0.1.1 ./langchain-demo
./hack/import-local-image-to-k3s.sh langchain-demo 0.1.1
```

### Install or upgrade

```bash
helm dependency build .
helm upgrade --install llm-observability-stack . \
  -n llm-observability --create-namespace \
  -f values.local-k3s.yaml
```

## Local browser/API access

- Open WebUI: `http://localhost:8080/`
- Ollama API and LangChain demo API are internal by default; use port-forward when needed:

```bash
kubectl port-forward -n llm-observability svc/ollama 11434:11434
kubectl port-forward -n llm-observability svc/langchain-demo 8000:8000
```

## LangSmith tracing for Open WebUI chats

Open WebUI now routes Ollama traffic through a traced proxy path in `langchain-demo`:

- Open WebUI Ollama base URL: `http://langchain-demo:8000/ollama`
- Proxy forwards to upstream Ollama: `http://ollama:11434`
- Proxy endpoint shape: `/ollama/api/*`

This keeps Open WebUI behavior Ollama-compatible while emitting LangSmith runs for chat requests.


## Python toolbox

`python-toolbox` is optional and currently disabled in the local profile to reduce RAM usage.

Enable it only when needed:

```bash
helm upgrade --install llm-observability-stack . \
  -n llm-observability --create-namespace \
  -f values.local-k3s.yaml \
  --set pythonToolbox.enabled=true
```

The 5-minute LangSmith seeder job is also disabled in this profile to avoid continuous background inference load.

### Jupyter note

The default toolbox command is `sleep infinity` because the chart is currently focused on shell-based in-cluster triage.

If you need JupyterLab, run it on the host and keep the `python-toolbox` pod for cluster-side connectivity checks.

## Model workflow

1. Put your GGUF file on host.
2. Mount the GGUF directory to `/models/gguf` in Ollama.
3. Use `__GGUF_PATH__` in Modelfile `FROM` line (chart replaces it at render time).
4. Ollama creates the model at startup from ConfigMap-backed Modelfile.

## etcd guidance

Keep `etcd.enabled: false` unless you are deliberately simulating one of these support scenarios:

- application works until a backing KV store becomes unavailable
- service dependency DNS/connectivity failures
- persistence-related startup or readiness issues

If you are not actively testing those scenarios, leaving etcd disabled keeps the stack smaller and easier to explain.

## Validation

Local validation:

```bash
helm lint .
helm template llm-observability-stack . > /tmp/rendered-default.yaml
helm template llm-observability-stack . -f values.local-k3s.example.yaml > /tmp/rendered-local.yaml
```

CI validation is included in `.github/workflows/helm-validate.yaml`.

## GitHub workflow

1. Create a feature branch from `main`.
2. Run local validation commands listed above.
3. Open a PR with change summary and validation evidence.
4. Keep secret-bearing changes out of git-tracked files.

## Repository hygiene

This repository intentionally excludes local secrets and generated files via `.gitignore`, including:

- `values.local-k3s.yaml`
- `.webui_secret_key`
- `rendered.yaml`
- model binaries like `*.gguf`
- local screenshots in `pictures/`

Use only `values.local-k3s.example.yaml` in git.

## Troubleshooting

- If browser access fails on localhost, check service types:
  - `kubectl get svc -n llm-observability open-webui ollama langchain-demo`
- If pods are healthy but services are `ClusterIP`, use `kubectl port-forward`.
- If GPU scheduling fails, verify:
  - `kubectl get nodes -o json | jq '.items[0].status.allocatable'`
  - `kubectl get pods -n nvidia-device-plugin`
- If your node exposes only `nvidia.com/gpu.shared` (MPS), request that resource in values and keep `ollama.ollama.gpu.number: 1`.
- In this environment, device-plugin runtime logs show `failRequestsGreaterThanOne: true` even when the ConfigMap sets `false`, so per-pod requests above `1` fail with `maximum request size for shared resources is 1`.
- To confirm what the plugin is enforcing at runtime:
  - `kubectl -n nvidia-device-plugin logs pod/$(kubectl -n nvidia-device-plugin get pod -l app.kubernetes.io/component=device-plugin -o jsonpath='{.items[0].metadata.name}') -c nvidia-device-plugin-ctr | grep -A8 '"mps"'`
- To confirm real GPU compute, run a chat request and sample host GPU:
  - `watch -n 0.5 nvidia-smi`
  - `kubectl port-forward -n llm-observability svc/ollama 11434:11434`
  - `curl -s http://localhost:11434/api/chat -d '{"model":"gemma3-1b-it-gguf-local","stream":false,"messages":[{"role":"user","content":"explain kubernetes rollout strategy"}]}' -H 'Content-Type: application/json'`
- If `langchain-demo` does not start, confirm the local image exists in k3s containerd:
  - `sudo k3s ctr images ls | grep langchain-demo`


## Lean local image workflow

For k3s, prefer building directly into containerd with `nerdctl --namespace k8s.io` when available. The helper scripts in `hack/` support that flow and fall back to Docker only if `nerdctl` is not installed.

The `python-toolbox` image is intentionally minimal and does not include JupyterLab. Run scripts with `kubectl exec` instead.
