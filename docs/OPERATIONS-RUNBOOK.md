# Operations Runbook

This runbook collects the day-0 and day-1 commands you are most likely to need while operating `llm-observability-stack` on a local k3s machine.

## 1. Before You Change Anything

Check current state:

```bash
kubectl get all -n llm-observability
kubectl get svc -n llm-observability
helm list -n llm-observability
git status --short
```

## 2. Build and Refresh Local Images

### Rebuild `langchain-demo`

```bash
./hack/build-local-image.sh langchain-demo 0.1.1 ./langchain-demo
./hack/import-local-image-to-k3s.sh langchain-demo 0.1.1
kubectl rollout restart deploy/langchain-demo -n llm-observability
kubectl rollout status deploy/langchain-demo -n llm-observability
```

### Rebuild `python-toolbox`

```bash
./hack/build-local-image.sh python-toolbox 0.2.0 ./python-toolbox
./hack/import-local-image-to-k3s.sh python-toolbox 0.2.0
kubectl rollout restart deploy/python-toolbox -n llm-observability
kubectl rollout status deploy/python-toolbox -n llm-observability
```

## 3. Install, Upgrade, and Roll Back

### Install or upgrade

```bash
helm dependency build .
helm upgrade --install llm-observability-stack . \
  -n llm-observability --create-namespace \
  -f values.local-k3s.yaml
```

### Inspect release values

```bash
helm get values llm-observability-stack -n llm-observability -a
```

### Review history and rollback

```bash
helm history llm-observability-stack -n llm-observability
helm rollback llm-observability-stack <REVISION> -n llm-observability
```

### Uninstall

```bash
helm uninstall llm-observability-stack -n llm-observability
```

## 4. Health Checks

### Basic workload checks

```bash
kubectl get pods -n llm-observability -o wide
kubectl get svc -n llm-observability
kubectl get pvc -n llm-observability
kubectl top pods -n llm-observability
```

### Service-specific logs

```bash
kubectl logs -n llm-observability deploy/langchain-demo --tail=100
kubectl logs -n llm-observability deploy/ollama --tail=100
kubectl logs -n llm-observability statefulset/open-webui --tail=100
kubectl logs -n llm-observability deploy/python-toolbox --tail=100
```

## 5. Access Internal APIs

```bash
kubectl port-forward -n llm-observability svc/ollama 11434:11434
kubectl port-forward -n llm-observability svc/langchain-demo 8000:8000
```

Use these for:

- direct Ollama API tests
- LangChain proxy notebook cells
- LangSmith traced proxy requests from the host

## 6. Jupyter Notebook Operations

Launch:

```bash
cd jupyter-notebooks
/usr/local/bin/python3.11 -m jupyter lab
```

Useful pairings:

- `01` before any major change
- `07` when validating `python-toolbox`
- `09` when validating cluster networking

If notebook cells fail:

- confirm the required port-forwards
- confirm the release is installed
- confirm the toolbox pod is running
- confirm LangSmith environment variables for tracing notebooks

## 7. In-Cluster Toolbox Checks

Open a shell:

```bash
kubectl exec -it -n llm-observability deploy/python-toolbox -- bash
```

Run helper scripts:

```bash
kubectl exec -it -n llm-observability deploy/python-toolbox -- python /workspace/examples/service_dns_check.py
kubectl exec -it -n llm-observability deploy/python-toolbox -- python /workspace/examples/ollama_smoke.py
kubectl exec -it -n llm-observability deploy/python-toolbox -- python /workspace/examples/redis_ping.py
```

## 8. GPU Checks

```bash
watch -n 0.5 nvidia-smi
kubectl get pods -n nvidia-device-plugin
kubectl get nodes -o json | jq '.items[0].status.allocatable'
```

If scheduling is failing, inspect the node plugin runtime behavior and confirm the resource name requested in `values.local-k3s.yaml`.

## 9. Troubleshooting Patterns

### `open-webui` works but notebooks fail

- likely missing `kubectl port-forward` for `ollama` and/or `langchain-demo`

### `langchain-demo` is unhealthy

- inspect logs
- confirm the local image tag imported into k3s matches the chart values
- confirm LangSmith env inputs are valid when tracing is enabled

### `ollama` is healthy but model calls fail

- verify GGUF host path mounts
- verify Modelfile render values
- verify the model exists through `/api/tags`

### `python-toolbox` is present but scripts are missing

- rebuild/import the local `python-toolbox` image
- restart the toolbox deployment

## 10. Cleanup and Hygiene

Do not commit:

- `values.local-k3s.yaml`
- notebook checkpoint directories
- generated notebook assets
- rendered manifests
- secret material
- large model binaries

Before publishing:

```bash
git status --short
helm lint .
pytest -q tests
```
