# EdgeLLM Observability Platform

Kubernetes-native observability and benchmarking for private GGUF/NVIDIA LLM inference on Linux edge devices, laptops, workstations, and small GPU clusters.

This repository packages an edge-focused LLM observability stack around k3s, Helm, NVIDIA GPU runtime/device plugin, Ollama/GGUF models, Open WebUI, a LangChain/LangSmith-compatible proxy, Prometheus, Grafana, blackbox probes, benchmark metrics, and NVIDIA/DCGM-ready dashboards.

GitHub repository: <https://github.com/waqasm86/llm-observability-stack>

## NVIDIA Inception 2026 Positioning

This project is being prepared for NVIDIA Inception Grand Challenge 2026 as a pilot-ready EdgeLLM observability platform. The core thesis is that enterprises adopting private LLMs on NVIDIA-powered Linux laptops, workstations, and edge nodes need a repeatable way to deploy, benchmark, monitor, and troubleshoot local inference before scaling to larger NVIDIA GPU fleets.

The current platform provides:

- Edge LLM deployment on Linux laptops and workstations.
- Local private GGUF model serving through Ollama.
- Kubernetes-native deployment through k3s and Helm.
- NVIDIA GPU scheduling through `runtimeClassName: nvidia` and `nvidia.com/gpu`.
- LLM request metrics for TTFT, latency, tokens per second, prompt tokens, generated tokens, active requests, and error rate.
- GPU and infrastructure views for utilization, framebuffer memory, power, temperature, and a DCGM-compatible dashboard.
- Reproducible benchmark and competition evidence under [docs/competition](docs/competition).
- A verified GeForce 940M profile as a low-cost edge feasibility proof.
- A scale path to RTX laptops/workstations, Jetson and edge boxes, NVIDIA GPU Operator/DCGM, NIM, and NCP or other cloud GPU clusters.

> **Readiness boundary:** This repository is pilot-ready and production-oriented, but not yet customer-production-proven. Customer/design-partner validation, security review, and multi-device benchmark evidence are required before claiming enterprise production readiness. NVIDIA and Lenovo have not endorsed or certified this project.

## Verified Edge Proof: GeForce 940M

The verified local edge profile runs on:

- Host: Lenovo ThinkPad T450s on Xubuntu 24.
- GPU: NVIDIA GeForce 940M, 1 GiB VRAM, CUDA compute capability 5.0.
- k3s node: combined control-plane and worker.
- NVIDIA device plugin resource: `nvidia.com/gpu: 1`.
- RuntimeClass: `nvidia`.
- Model: Gemma 3 1B IT Q4_K_M GGUF, approximately 806 MB.

Measured after one warmup and three streaming benchmark requests:

| Metric | Result |
|---|---:|
| TTFT p50 | 0.377 s |
| TTFT p95 | 0.381 s |
| Mean throughput | 11.69 tokens/s |
| End-to-end p95 | 6.97 s |
| Peak GPU utilization | 52% |
| VRAM usage | 554 MiB |

Evidence and reproduction:

- [Single-node k3s GeForce 940M guide](docs/SINGLE-NODE-K3S-GEFORCE-940M.md)
- [Verified local results](docs/competition/VERIFIED-LOCAL-RESULTS.md)
- [Sanitized benchmark artifact](artifacts/geforce-940m-benchmark.json)
- [GeForce 940M Helm profile](values.geforce-940m-k3s.yaml)

These numbers prove constrained edge feasibility. They do not establish enterprise load, concurrency, fleet reliability, or production readiness.

## Who This Is For

- Enterprise AI/platform teams evaluating private local LLMs.
- IT teams deploying NVIDIA-powered Linux laptops/workstations.
- Field engineering teams needing offline/private AI.
- Universities and AI labs with low-cost GPU fleets.
- OEM/SI partners validating AI workstation bundles.
- NVIDIA/Lenovo-style edge AI demo and pilot teams.

## What This Is Not

- Not a generic cloud-only LLM observability SaaS.
- Not a replacement for LangSmith, Grafana, Prometheus, DCGM, or NIM.
- Not a claim that every NVIDIA laptop is production-ready for LLM inference.
- Not an NVIDIA- or Lenovo-certified product yet.
- Not a repository for committing GGUF model binaries or secrets.

## Platform Components

- Vendored Ollama and Open WebUI Helm charts.
- FastAPI LangChain/LangSmith-compatible proxy with Prometheus metrics.
- TTFT, latency, token, throughput, active-request, HTTP, and error telemetry.
- Optional kube-prometheus-stack, Grafana, Alertmanager, node exporter, and kube-state-metrics.
- Blackbox endpoint probes and Prometheus alert rules.
- NVIDIA DCGM dashboard and external DCGM ServiceMonitor integration.
- NVIDIA NIM `/v1/metrics` ServiceMonitor path.
- Pushgateway-compatible benchmark reporting.
- Optional Python diagnostics toolbox, Redis, LangSmith seeder, and etcd failure simulation.

## Runtime Architecture

```text
User or benchmark client
        |
        v
Open WebUI / FastAPI proxy
        |                \
        |                 +--> LangSmith-compatible traces
        |                 +--> Prometheus /metrics
        v
Ollama + private GGUF model       Optional NVIDIA NIM
        |                              |
        +---------- NVIDIA GPU --------+
                         |
                  DCGM / GPU metrics

Prometheus + Grafana + Alertmanager
        ^
        +-- ServiceMonitors, probes, benchmark Pushgateway, Kubernetes metrics
```

The verified laptop profile uses Ollama/GGUF. The enterprise scale path can retain the observability contract while moving inference to RTX workstations, GPU Operator/DCGM clusters, NIM, or cloud GPUs.

## Repository Layout

```text
llm-observability-stack/
├── Chart.yaml
├── values.yaml
├── values.validation-k3s.yaml
├── values.geforce-940m-k3s.yaml
├── values.competition-nvidia.example.yaml
├── values.local-k3s.example.yaml
├── artifacts/                     # sanitized public benchmark evidence
├── benchmarks/                    # repeatable inference benchmark clients
├── dashboards/                    # LLM, benchmark, and NVIDIA GPU dashboards
├── monitoring/                    # pinned Prometheus Community umbrella chart
├── templates/                     # application monitoring and security manifests
├── charts/                        # vendored Ollama and Open WebUI charts
├── langchain-demo/                # instrumented FastAPI proxy
├── python-toolbox/                # in-cluster diagnostics
├── docs/
│   └── competition/               # pitch, pilot, evidence, and readiness package
├── hack/                          # validation, device-plugin, and evidence scripts
└── tests/                         # Helm and application smoke tests
```

## Prerequisites

- Linux host or cluster with k3s/Kubernetes reachable through `kubectl`.
- Helm 3 or 4.
- NVIDIA driver and NVIDIA Container Toolkit for GPU profiles.
- NVIDIA device plugin or GPU Operator exposing `nvidia.com/gpu`.
- A legally obtained GGUF model available on node storage.
- Python 3.11 for tests and benchmark tooling.

Quick checks:

```bash
kubectl get nodes -o wide
kubectl get runtimeclass nvidia
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
helm version
```

## Quick Start

### A. Minimal validation profile

```bash
helm template llm-observability-stack . \
  -f values.validation-k3s.yaml
```

### B. Verified GeForce 940M edge profile

Review the machine-specific model host path before using this profile on another system.

```bash
./hack/prepare-single-node-k3s.sh
./hack/install-nvidia-device-plugin.sh

helm upgrade --install llm-observability-stack . \
  -n llm-observability --create-namespace \
  -f values.geforce-940m-k3s.yaml

./hack/test-geforce-940m-inference.sh
```

### C. Full competition profile

```bash
helm dependency build monitoring

helm upgrade --install llm-monitoring ./monitoring \
  -n monitoring --create-namespace

helm upgrade --install llm-observability-stack . \
  -n llm-observability --create-namespace \
  -f values.competition-nvidia.example.yaml
```

Use private values files or existing Kubernetes Secrets for LangSmith and Open WebUI secrets. Never commit secrets.

## Access and Benchmarking

```bash
kubectl get pods -n llm-observability -o wide
kubectl port-forward -n llm-observability svc/ollama 11434:11434
```

Run the public benchmark from another terminal:

```bash
./benchmarks/ollama_benchmark.py \
  --model gemma3-1b-it-gguf-local \
  --warmup-runs 1 \
  --runs 10 \
  --output artifacts/benchmark-local.json
```

Only sanitized evidence intended for publication should be committed.

## Validation

```bash
helm lint .
helm template llm-observability-stack . >/tmp/rendered-default.yaml
helm template llm-observability-stack . \
  -f values.geforce-940m-k3s.yaml >/tmp/rendered-geforce.yaml
helm template llm-observability-stack . \
  -f values.competition-nvidia.example.yaml \
  --set langsmith.existingSecret= \
  --set openWebUI.existingSecret= \
  --set open-webui.webuiSecret.existingSecretName= \
  >/tmp/rendered-competition.yaml

helm dependency build monitoring
helm lint monitoring
pytest -q tests
./hack/competition-validate.sh
./hack/competition-validate.sh --strict-gpu
```

The strict GPU check requires an active cluster with an allocatable NVIDIA GPU.

## Competition and Pilot Package

- [Competition entry point](docs/competition/README.md)
- [Pitch deck outline](docs/competition/PITCH-DECK-OUTLINE.md)
- [Pilot proposal template](docs/competition/PILOT-PROPOSAL-TEMPLATE.md)
- [Edge validation roadmap](docs/competition/EDGE-VALIDATION-ROADMAP.md)
- [EdgeLLM business model](docs/competition/EDGE-BUSINESS-MODEL.md)
- [Lenovo/OEM edge AI angle](docs/competition/LENOVO-OEM-ANGLE.md)
- [Readiness matrix](docs/competition/READINESS-MATRIX.md)
- [Evidence checklist](docs/competition/EVIDENCE-CHECKLIST.md)

## Security and Evidence Boundaries

- Use `existingSecret` references or private ignored values files.
- Keep prompt and response capture disabled or redacted for confidential workloads.
- Do not commit model binaries, kubeconfigs, private customer evidence, credentials, or TLS keys.
- Treat host-path model mounts and `local-path` persistence as edge-reference defaults, not universal production storage.
- Complete TLS, SSO/RBAC, backup, retention, network-policy, and threat-model review for each pilot.

## Troubleshooting

```bash
kubectl get pods -A -o wide
kubectl describe pod -n llm-observability -l app.kubernetes.io/name=ollama
kubectl logs -n llm-observability deployment/ollama --tail=200
kubectl get pods -n nvidia-device-plugin
kubectl get nodes -o json | jq '.items[].status.allocatable'
watch -n 0.5 nvidia-smi
```

The first Ollama image pull can be several gigabytes and may exceed a short Helm wait timeout. Once cached, rerun the same `helm upgrade --install` command to reconcile the release.

## Documentation

Start with [docs/README.md](docs/README.md), then use:

- [Architecture](docs/ARCHITECTURE.md)
- [Configuration profiles](docs/CONFIG-PROFILES.md)
- [Operations runbook](docs/OPERATIONS-RUNBOOK.md)
- [Complete project documentation](docs/PROJECT-DOCUMENTATION.md)
- [GitHub publishing guide](docs/GITHUB-PUBLISHING.md)

## Project Status

EdgeLLM Observability Platform is an open-source, pilot-ready reference implementation with verified local NVIDIA edge evidence. The next proof requirements are a modern RTX laptop benchmark, workstation and cloud GPU comparisons, security review, and a real design-partner pilot with documented measurable outcomes.
