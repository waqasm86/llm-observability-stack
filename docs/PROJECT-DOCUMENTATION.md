# llm-observability-stack: Complete Project Documentation

Use this document as the deep reference after the focused guides:

- [QUICKSTART.md](QUICKSTART.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [OPERATIONS-RUNBOOK.md](OPERATIONS-RUNBOOK.md)

## 1. Purpose and Scope

`llm-observability-stack` is an umbrella Helm chart for local single-node Kubernetes (k3s) deployments with NVIDIA GPU support.

Primary goals:

- Run local LLM inference with Ollama using GGUF models.
- Provide UI access through Open WebUI.
- Provide an API integration surface through a FastAPI + LangChain demo app.
- Provide observability and connectivity triage via LangSmith and an in-cluster Python toolbox.

This chart is optimized for local workstation workflows and interview/demo troubleshooting scenarios.

## 2. Architecture Overview

### 2.1 Top-level architecture

- Umbrella chart: `llm-observability-stack`
- Vendored dependency charts:
  - `charts/ollama`
  - `charts/open-webui`
- Custom glue resources in `templates/`:
  - LangSmith Secret (optional)
  - Open WebUI Secret (optional)
  - Ollama Modelfile ConfigMap
  - LangChain demo app ConfigMap (optional mount-over-image mode)
  - LangChain demo Deployment + Service
  - Python toolbox Deployment (optional)
  - LangSmith dashboard seeder CronJob (optional)
  - Optional Redis Deployment/Service/PVC/Secret
  - Optional etcd StatefulSet + Services

### 2.2 Runtime traffic paths

1. User -> Open WebUI (`open-webui:8080`)
2. Open WebUI -> LangChain demo proxy (`langchain-demo:8000/ollama`)
3. LangChain demo proxy -> Ollama (`OLLAMA_UPSTREAM_BASE_URL=http://ollama:11434`)
4. LangChain demo -> LangSmith API for proxy traces (when configured)
5. Optional Python toolbox -> LangSmith API (when enabled)
5. Open WebUI websocket manager -> Redis
   - Default: subchart `open-webui-redis`
   - Optional: custom `redis` resource from root templates

## 3. Repository Structure

```text
llm-observability-stack/
├── Chart.yaml
├── Chart.lock
├── values.yaml
├── values.local-k3s.example.yaml
├── values.local-k3s.yaml          # local only, gitignored
├── templates/                     # root custom manifests
├── charts/
│   ├── ollama/                    # vendored dependency
│   └── open-webui/                # vendored dependency
├── langchain-demo/                # FastAPI app image source
├── python-toolbox/                # debug image source + scripts
├── hack/                          # local image build/import helpers
├── files/                         # pre/post change cluster snapshots
└── docs/                          # documentation
```

## 4. Component Details

### 4.1 Ollama

- Deployed via vendored Ollama chart.
- GPU support enabled by values.
- Model creation at startup from ConfigMap-backed Modelfile.
- Persistent model storage with PVC (`local-path` by default).

Key value paths:

- `ollama.enabled`
- `ollama.runtimeClassName`
- `ollama.ollama.gpu.*`
- `ollama.ollama.models.create[]`
- `ollama.persistentVolume.*`
- `ollama.volumes[]` and `ollama.volumeMounts[]`

### 4.2 Open WebUI

- Deployed via vendored Open WebUI chart.
- Configured to use Ollama endpoint in-cluster.
- Websocket support enabled.
- Persistence enabled using PVC.

Key value paths:

- Dependency gate: `openWebUI.enabled`
- Subchart runtime config: `open-webui.*`
- Secret input wrapper: `openWebUI.webuiSecretKey` and `openWebUI.existingSecret`

### 4.3 LangChain demo service

- Containerized FastAPI app in `langchain-demo/app.py`.
- Exposes:
  - `GET /`
  - `GET /healthz`
  - `GET /config`
  - `POST /invoke`
- Uses `langchain-ollama` (`ChatOllama`) against Ollama API.
- Can emit tracing to LangSmith when API key is configured.

### 4.4 Python toolbox

- Utility pod for in-cluster diagnosis.
- Ships troubleshooting scripts for:
  - DNS/service checks
  - Ollama chat smoke
  - Redis ping
  - LangSmith API health

### 4.5 Optional Redis (root template)

- Disabled by default.
- If enabled, deploys Secret + ConfigMap + PVC + Deployment + Service.
- Supports Redis ACL auth (`redis.auth.enabled=true`).

### 4.6 Optional etcd

- Disabled by default.
- Deploys single or multi replica StatefulSet depending on `etcd.replicaCount`.
- Intended for targeted troubleshooting scenarios.

## 5. Values and Configuration Strategy

Use a 3-file strategy:

- `values.yaml`: non-secret, stable defaults tracked in git.
- `values.local-k3s.example.yaml`: sanitized local template tracked in git.
- `values.local-k3s.yaml`: machine + secret overrides, **gitignored**.

Recommended install command:

```bash
helm dependency build .
helm upgrade --install llm-observability-stack . \
  -n llm-observability --create-namespace \
  -f values.local-k3s.yaml
```

## 6. Prerequisites

- k3s cluster running and reachable by `kubectl`
- NVIDIA runtime configured on node
- NVIDIA device plugin healthy in cluster
- Helm 3 installed
- Docker or nerdctl available for local image workflows
- GGUF model file available on host filesystem

Quick prerequisite checks:

```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get pods -n nvidia-device-plugin
helm version
```

## 7. Build and Image Workflow

### 7.1 Build local images

```bash
./hack/build-local-image.sh langchain-demo 0.1.1 ./langchain-demo
./hack/build-local-image.sh python-toolbox 0.2.0 ./python-toolbox
```

### 7.2 Import images into k3s containerd

```bash
./hack/import-local-image-to-k3s.sh langchain-demo 0.1.1
./hack/import-local-image-to-k3s.sh python-toolbox 0.2.0
```

### 7.3 Verify images

```bash
sudo k3s ctr images ls | grep -E 'langchain-demo|python-toolbox'
```

## 8. Deploy, Validate, and Upgrade

### 8.1 Lint and render before deploy

```bash
helm lint .
helm template llm-observability-stack . > /tmp/rendered-default.yaml
helm template llm-observability-stack . -f values.local-k3s.example.yaml > /tmp/rendered-example.yaml
```

### 8.2 Deploy

```bash
helm upgrade --install llm-observability-stack . \
  -n llm-observability --create-namespace \
  -f values.local-k3s.yaml
```

### 8.3 Post-deploy checks

```bash
kubectl get all -n llm-observability
kubectl get pvc -n llm-observability
kubectl get pods -n llm-observability -o wide
kubectl get svc -n llm-observability
```

### 8.4 Upgrade

```bash
helm dependency build .
helm upgrade llm-observability-stack . \
  -n llm-observability \
  -f values.local-k3s.yaml
```

### 8.5 Rollback

```bash
helm history llm-observability-stack -n llm-observability
helm rollback llm-observability-stack <REVISION> -n llm-observability
```

## 9. Runtime Endpoints

Typical service endpoints in namespace:

- Ollama: `http://ollama:11434`
- Open WebUI: `http://open-webui:8080`
- LangChain demo: `http://langchain-demo:8000`

Local access options:

- expose only required services as `LoadBalancer` in local k3s overrides
- or `kubectl port-forward`

Example:

```bash
kubectl port-forward -n llm-observability svc/open-webui 8080:8080
kubectl port-forward -n llm-observability svc/ollama 11434:11434
kubectl port-forward -n llm-observability svc/langchain-demo 8000:8000
```

## 10. Health and Observability Workflow

### 10.1 Basic health checks

```bash
kubectl get pods -n llm-observability
kubectl logs -n llm-observability deploy/langchain-demo --tail=100
kubectl logs -n llm-observability deploy/ollama --tail=100
kubectl logs -n llm-observability statefulset/open-webui --tail=100
```

### 10.2 LangChain demo API

```bash
kubectl port-forward -n llm-observability svc/langchain-demo 8000:8000
curl -s http://localhost:8000/healthz | jq
curl -s http://localhost:8000/config | jq
curl -s http://localhost:8000/invoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Say hello in one short sentence."}' | jq
```

### 10.3 Python toolbox checks

Only when `pythonToolbox.enabled=true`.

```bash
kubectl exec -it -n llm-observability deploy/python-toolbox -- bash
python /workspace/examples/service_dns_check.py
python /workspace/examples/ollama_smoke.py
python /workspace/examples/redis_ping.py
python /workspace/examples/langsmith_healthcheck.py
python /workspace/examples/langsmith_inference_traces.py
python /workspace/examples/langsmith_dashboard_seed_every_5m.py
```

## 11. Security Guidance

- Keep secrets only in local untracked files or external secrets.
- Do not commit real values in `values.local-k3s.yaml`.
- Never print or paste secret values into issue trackers.
- Consider using `existingSecret` references backed by manually managed Kubernetes secrets.
- Restrict service exposure when not required (avoid broad `LoadBalancer` in shared environments).

## 12. Common Failure Modes and Fixes

### 12.1 `ImagePullBackOff` on langchain-demo or python-toolbox

Cause:

- local images were not built/imported to k3s runtime.

Fix:

```bash
./hack/build-local-image.sh langchain-demo 0.1.1 ./langchain-demo
./hack/import-local-image-to-k3s.sh langchain-demo 0.1.1
./hack/build-local-image.sh python-toolbox 0.2.0 ./python-toolbox
./hack/import-local-image-to-k3s.sh python-toolbox 0.2.0
kubectl rollout restart deploy/langchain-demo -n llm-observability
# only if enabled
kubectl rollout restart deploy/python-toolbox -n llm-observability
```

### 12.2 Ollama model not available

Cause:

- GGUF host path mismatch or model filename mismatch.

Fix:

```bash
kubectl describe pod -n llm-observability deploy/ollama
kubectl logs -n llm-observability deploy/ollama --tail=200
kubectl exec -it -n llm-observability deploy/ollama -- ls -lah /models/gguf
kubectl exec -it -n llm-observability deploy/ollama -- ollama list
```

### 12.3 Open WebUI cannot reach Ollama

Cause:

- service DNS mismatch, endpoint not ready, or wrong `ollamaUrls`.

Fix:

```bash
kubectl get svc -n llm-observability ollama open-webui
kubectl get endpoints -n llm-observability ollama open-webui
kubectl exec -it -n llm-observability deploy/python-toolbox -- python /workspace/examples/service_dns_check.py
```

### 12.4 Websocket or chat instability with Redis

Cause:

- mismatch between Open WebUI websocket URL and deployed Redis mode.

Fix:

```bash
kubectl get deploy,svc -n llm-observability | grep -E 'open-webui-redis|redis'
kubectl logs -n llm-observability statefulset/open-webui --tail=200
kubectl logs -n llm-observability deploy/redis --tail=200
```

## 13. Data Persistence

Default persisted data:

- Ollama model/data PVC
- Open WebUI PVC
- Optional Redis PVC
- Optional etcd PVCs

Check storage state:

```bash
kubectl get pvc -n llm-observability
kubectl describe pvc -n llm-observability
```

## 14. CI and Collaboration

- CI currently validates Helm syntax and rendering.
- Refer to `docs/GITHUB-PUBLISHING.md` for publish process.
- Use issue/PR templates in `.github/` for reproducible reports.

## 15. Related Documentation

- `docs/KUBECTL-COMMAND-REFERENCE.md`
- `docs/KUBERNETES-NETWORKING.md`
- `docs/PYTHON-KUBERNETES-AUTOMATION.md`
- `docs/GITHUB-PUBLISHING.md`
