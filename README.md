# llm-observability-stack

`llm-observability-stack` is an umbrella Helm chart for a local, single-node, GPU-capable k3s workstation. It packages a practical LLM demo environment around Ollama, Open WebUI, a LangChain-based proxy/demo API, LangSmith tracing, and an optional in-cluster Python toolbox for diagnostics.

GitHub repository: <https://github.com/waqasm86/llm-observability-stack>

## What This Repository Is For

- Local k3s + NVIDIA workstation experiments
- GGUF-based Ollama model serving
- Open WebUI chat demos on a single node
- LangSmith-traced proxy traffic for observability walkthroughs
- Kubernetes networking, notebook, and troubleshooting exercises

## What It Deploys

- Vendored `ollama` Helm chart in [charts/ollama](charts/ollama)
- Vendored `open-webui` Helm chart in [charts/open-webui](charts/open-webui)
- A local FastAPI-based LangChain demo/proxy in [langchain-demo](langchain-demo)
- An in-cluster Python toolbox image in [python-toolbox](python-toolbox)
- Optional Redis resources for Open WebUI websocket/state flows
- Optional LangSmith dashboard seeder CronJob
- Optional etcd simulation resources for troubleshooting drills
- Custom root templates in [templates](templates) that glue the stack together

## Runtime Architecture

Primary request path:

1. Browser -> `open-webui` (`LoadBalancer` on local k3s)
2. `open-webui` -> `langchain-demo` proxy (`/ollama/api/*`)
3. `langchain-demo` -> `ollama`
4. `langchain-demo` -> LangSmith API when tracing is configured
5. `python-toolbox` -> in-cluster DNS/service checks and optional LangSmith support scripts

Typical local exposure strategy:

- `open-webui` is exposed directly for browser use
- `ollama` and `langchain-demo` stay `ClusterIP`
- host access to internal APIs is done with `kubectl port-forward`
- `pythonToolbox.enabled: true` in the local k3s profile

## Repository Layout

```text
llm-observability-stack/
├── Chart.yaml
├── values.yaml
├── values.local-k3s.example.yaml
├── templates/                     # root chart manifests
├── charts/                        # vendored dependency charts
├── langchain-demo/                # local image source for proxy/demo API
├── python-toolbox/                # local image source for in-cluster helpers
├── jupyter-notebooks/             # notebook walkthroughs and diagnostics
├── docs/                          # extended project documentation
├── hack/                          # local image build/import helpers
└── tests/                         # smoke tests and chart checks
```

## Documentation Map

Core documentation:

- [docs/README.md](docs/README.md)
- [docs/QUICKSTART.md](docs/QUICKSTART.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/OPERATIONS-RUNBOOK.md](docs/OPERATIONS-RUNBOOK.md)
- [docs/NOTEBOOKS-GUIDE.md](docs/NOTEBOOKS-GUIDE.md)
- [docs/PROJECT-DOCUMENTATION.md](docs/PROJECT-DOCUMENTATION.md)
- [docs/KUBERNETES-NETWORKING.md](docs/KUBERNETES-NETWORKING.md)
- [docs/KUBECTL-COMMAND-REFERENCE.md](docs/KUBECTL-COMMAND-REFERENCE.md)
- [docs/PYTHON-KUBERNETES-AUTOMATION.md](docs/PYTHON-KUBERNETES-AUTOMATION.md)
- [docs/GITHUB-PUBLISHING.md](docs/GITHUB-PUBLISHING.md)

Component documentation:

- [langchain-demo/README.md](langchain-demo/README.md)
- [python-toolbox/README.md](python-toolbox/README.md)
- [hack/README.md](hack/README.md)
- [jupyter-notebooks/README.md](jupyter-notebooks/README.md)
- [jupyter-notebooks/llm-observability-in-action/README.md](jupyter-notebooks/llm-observability-in-action/README.md)

## Prerequisites

- k3s cluster reachable from `kubectl`
- NVIDIA runtime configured on the node
- NVIDIA device plugin already installed in the cluster
- Helm 3
- Docker or `nerdctl`
- A local GGUF model file on host storage
- Python 3.11 for notebook workflows

Recommended quick checks:

```bash
kubectl get nodes -o wide
kubectl get pods -n nvidia-device-plugin
helm version
```

## Quick Start

1. Copy the local values template:

```bash
cp values.local-k3s.example.yaml values.local-k3s.yaml
```

2. Edit `values.local-k3s.yaml` and set:

- the GGUF host path values for Ollama
- LangSmith credentials or existing secret references
- Open WebUI secret handling

3. Build/import local images:

```bash
./hack/build-local-image.sh langchain-demo 0.1.1 ./langchain-demo
./hack/import-local-image-to-k3s.sh langchain-demo 0.1.1
./hack/build-local-image.sh python-toolbox 0.2.0 ./python-toolbox
./hack/import-local-image-to-k3s.sh python-toolbox 0.2.0
```

4. Install or upgrade:

```bash
helm dependency build .
helm upgrade --install llm-observability-stack . \
  -n llm-observability --create-namespace \
  -f values.local-k3s.yaml
```

5. Verify:

```bash
kubectl get all -n llm-observability
kubectl get svc -n llm-observability
```

## Local Access Patterns

Browser access:

- Open WebUI: `http://localhost:8080/`

Port-forward internal APIs when needed:

```bash
kubectl port-forward -n llm-observability svc/ollama 11434:11434
kubectl port-forward -n llm-observability svc/langchain-demo 8000:8000
```

Notebook launch:

```bash
cd jupyter-notebooks
/usr/local/bin/python3.11 -m jupyter lab
```

## Common Workflows

### Rebuild `langchain-demo`

```bash
./hack/build-local-image.sh langchain-demo 0.1.1 ./langchain-demo
./hack/import-local-image-to-k3s.sh langchain-demo 0.1.1
kubectl rollout restart deploy/langchain-demo -n llm-observability
```

### Rebuild `python-toolbox`

```bash
./hack/build-local-image.sh python-toolbox 0.2.0 ./python-toolbox
./hack/import-local-image-to-k3s.sh python-toolbox 0.2.0
kubectl rollout restart deploy/python-toolbox -n llm-observability
```

### Disable toolbox temporarily

```bash
helm upgrade --install llm-observability-stack . \
  -n llm-observability --create-namespace \
  -f values.local-k3s.yaml \
  --set pythonToolbox.enabled=false
```

### Render manifests without applying

```bash
helm template llm-observability-stack . > /tmp/rendered-default.yaml
helm template llm-observability-stack . -f values.local-k3s.example.yaml > /tmp/rendered-example.yaml
```

## Validation

Recommended local validation:

```bash
helm lint .
helm template llm-observability-stack . > /tmp/rendered-default.yaml
helm template llm-observability-stack . -f values.local-k3s.example.yaml > /tmp/rendered-local.yaml
pytest -q tests
```

## Troubleshooting Highlights

- If `open-webui` is reachable but internal API notebooks fail, check port-forwards for `ollama` and `langchain-demo`.
- If `langchain-demo` is unhealthy, inspect:

```bash
kubectl logs -n llm-observability deploy/langchain-demo --tail=100
kubectl describe deploy -n llm-observability langchain-demo
```

- If Ollama is slow or unavailable, inspect:

```bash
kubectl logs -n llm-observability deploy/ollama --tail=100
kubectl top pods -n llm-observability
watch -n 0.5 nvidia-smi
```

- If GPU scheduling fails, inspect:

```bash
kubectl get pods -n nvidia-device-plugin
kubectl get nodes -o json | jq '.items[0].status.allocatable'
```

- If notebook diagnostics fail inside the cluster, inspect:

```bash
kubectl get pods -n llm-observability -l app.kubernetes.io/name=python-toolbox -o wide
kubectl exec -it -n llm-observability deploy/python-toolbox -- bash
```

## Git and Publishing

- GitHub remote: `origin -> https://github.com/waqasm86/llm-observability-stack.git`
- Publishing guide: [docs/GITHUB-PUBLISHING.md](docs/GITHUB-PUBLISHING.md)
- Local-only artifacts and secrets are excluded by [.gitignore](.gitignore)

Never commit:

- `values.local-k3s.yaml`
- `.env*`
- `.webui_secret_key`
- TLS keys/certs
- rendered debug manifests
- large model binaries
- notebook checkpoint directories

## Current Local Profile Notes

- `pythonToolbox.enabled: true`
- `langsmithDashboardSeeder.enabled: false`
- `open-webui` is intended for direct browser use
- `ollama` and `langchain-demo` are internal by default
- the stack is optimized for local Xubuntu + k3s + NVIDIA workflows, not generic multi-node production deployment
