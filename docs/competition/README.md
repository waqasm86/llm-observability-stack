# EdgeLLM Observability Platform: Competition Package

## Product

**Product name:** EdgeLLM Observability Platform

**Repository role:** Open-source Helm/k3s deployment engine for private LLM inference,
observability, benchmarking, dashboards, alerts, and evidence capture on NVIDIA-powered Linux edge
systems.

## Enterprise Problem

Enterprises buying NVIDIA-powered Linux laptops, workstations, and small edge nodes need measurable
local AI operations. Private LLM pilots are difficult to support when model latency, token
throughput, GPU use, memory pressure, endpoint health, and deployment configuration are split
across unrelated tools or absent entirely.

EdgeLLM Observability provides a repeatable reference stack for deploying, benchmarking, monitoring,
and troubleshooting private GGUF inference before a team scales to larger GPU fleets.

## Verified Evidence

The current low-cost edge proof runs on a Lenovo ThinkPad T450s with:

- NVIDIA GeForce 940M, 1 GiB VRAM, CUDA compute capability 5.0
- combined k3s control-plane and worker node
- NVIDIA device plugin exposing one `nvidia.com/gpu`
- Ollama 0.17.7
- Gemma 3 1B IT Q4_K_M GGUF

Measured results include 0.377-second TTFT p50, 11.69 generated tokens per second, 52% peak GPU
utilization, and 554 MiB model VRAM. See [VERIFIED-LOCAL-RESULTS.md](VERIFIED-LOCAL-RESULTS.md) and
the sanitized benchmark JSON in `artifacts/`.

## NVIDIA Alignment

- NVIDIA Container Runtime and Kubernetes `RuntimeClass: nvidia`
- NVIDIA device plugin and `nvidia.com/gpu` scheduling
- verified CUDA inference on local NVIDIA hardware
- DCGM-compatible GPU dashboards and alert rules
- ServiceMonitor integration for external DCGM Exporter
- NVIDIA NIM `/v1/metrics` ServiceMonitor path
- upward deployment path to GPU Operator, RTX workstations, edge clusters, NIM, and cloud GPUs

## Current Status

The repository is a pilot-ready, production-oriented reference stack. It is not yet a finished
enterprise product or customer-production-proven platform. Design-partner validation, security
review, and broader hardware evidence remain required.

## Next Evidence Targets

1. RTX laptop benchmark.
2. RTX workstation benchmark.
3. Cloud GPU benchmark.
4. One design-partner pilot with measurable outcomes.
5. Security and data-flow review.

## Competition Deliverables

- [PITCH-DECK-OUTLINE.md](PITCH-DECK-OUTLINE.md)
- [DEMO-RUNBOOK.md](DEMO-RUNBOOK.md)
- [PILOT-PROPOSAL-TEMPLATE.md](PILOT-PROPOSAL-TEMPLATE.md)
- [EDGE-BUSINESS-MODEL.md](EDGE-BUSINESS-MODEL.md)
- [LENOVO-OEM-ANGLE.md](LENOVO-OEM-ANGLE.md)
- [EDGE-VALIDATION-ROADMAP.md](EDGE-VALIDATION-ROADMAP.md)
- [READINESS-MATRIX.md](READINESS-MATRIX.md)
- [EVIDENCE-CHECKLIST.md](EVIDENCE-CHECKLIST.md)

NVIDIA and Lenovo have not endorsed, sponsored, or certified the project. Any future partner claims
must be supported by written evidence.
