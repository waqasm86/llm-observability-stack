# Quick Start

This guide is the fastest path to a working local `llm-observability-stack` deployment on a single-node k3s machine.

## 1. Prerequisites

- k3s running and reachable from `kubectl`
- NVIDIA runtime configured on the node
- NVIDIA device plugin already healthy in-cluster
- Helm 3 installed
- Docker or `nerdctl`
- local GGUF model file on host storage

Quick checks:

```bash
kubectl get nodes -o wide
kubectl get pods -n nvidia-device-plugin
helm version
```

## 2. Prepare Local Values

Create your local override file:

```bash
cp values.local-k3s.example.yaml values.local-k3s.yaml
```

Edit `values.local-k3s.yaml` and confirm:

- GGUF host path values point to your model directory
- LangSmith credentials or existing secret references are set correctly
- Open WebUI secret inputs are wired the way you want
- `pythonToolbox.enabled: true` if you want notebook-driven diagnostics available immediately

Do not commit `values.local-k3s.yaml`.

## 3. Build and Import Local Images

Build the local images:

```bash
./hack/build-local-image.sh langchain-demo 0.1.1 ./langchain-demo
./hack/build-local-image.sh python-toolbox 0.2.0 ./python-toolbox
```

Import them into k3s:

```bash
./hack/import-local-image-to-k3s.sh langchain-demo 0.1.1
./hack/import-local-image-to-k3s.sh python-toolbox 0.2.0
```

Verify:

```bash
sudo k3s ctr images ls | grep -E 'langchain-demo|python-toolbox'
```

## 4. Deploy the Chart

```bash
helm dependency build .
helm upgrade --install llm-observability-stack . \
  -n llm-observability --create-namespace \
  -f values.local-k3s.yaml
```

## 5. Verify the Deployment

```bash
kubectl get all -n llm-observability
kubectl get svc -n llm-observability
kubectl get pvc -n llm-observability
```

Typical local result:

- `open-webui` exposed for browser access
- `ollama` internal `ClusterIP`
- `langchain-demo` internal `ClusterIP`
- `python-toolbox` running for in-cluster diagnostics

## 6. Local Access

Browser:

- Open WebUI: `http://localhost:8080/`

Internal APIs:

```bash
kubectl port-forward -n llm-observability svc/ollama 11434:11434
kubectl port-forward -n llm-observability svc/langchain-demo 8000:8000
```

## 7. Jupyter Notebooks

Launch notebooks from the project notebook directory:

```bash
cd jupyter-notebooks
/usr/local/bin/python3.11 -m jupyter lab
```

Notebook index:

- `01` environment smoke test
- `02` Ollama API basics
- `03` LangChain proxy deep dive
- `04` LangSmith tracing setup
- `05` Open WebUI end-to-end flow
- `06` custom Modelfile workflow
- `07` python-toolbox diagnostics
- `08` troubleshooting and etcd simulations
- `09` k3s networking deep dive

## 8. Minimal Troubleshooting

If the stack does not come up cleanly:

```bash
kubectl get pods -n llm-observability -o wide
kubectl logs -n llm-observability deploy/langchain-demo --tail=100
kubectl logs -n llm-observability deploy/ollama --tail=100
kubectl logs -n llm-observability statefulset/open-webui --tail=100
```

If notebook API cells fail:

- verify the required port-forwards are active
- verify `pythonToolbox.enabled` and toolbox pod health
- verify LangSmith environment variables for tracing notebooks

## 9. Next Reading

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [OPERATIONS-RUNBOOK.md](OPERATIONS-RUNBOOK.md)
- [../jupyter-notebooks/README.md](../jupyter-notebooks/README.md)
