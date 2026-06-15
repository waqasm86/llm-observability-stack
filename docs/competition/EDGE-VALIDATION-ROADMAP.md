# EdgeLLM Validation Roadmap

## Phase 1: Current Verified Low-Cost Edge Proof

- Lenovo ThinkPad T450s
- NVIDIA GeForce 940M
- k3s and NVIDIA device plugin
- Ollama and Gemma 3 1B IT Q4_K_M GGUF
- published TTFT, throughput, VRAM, utilization, and temperature evidence

Status: implemented and locally verified.

## Phase 2: Modern RTX Laptop Proof

- RTX 3050, 4050, or 4060 laptop
- 1B, 3B, and 7B GGUF benchmarks
- power, thermal, battery/AC mode, and repeated-request comparison

Status: hardware and evidence required.

## Phase 3: Workstation Proof

- RTX A-series or Ada workstation
- larger GGUF model
- concurrent request and sustained-load testing
- reliability and support workflow measurements

Status: hardware and evidence required.

## Phase 4: NVIDIA Platform Proof

- NVIDIA GPU Operator and DCGM Exporter
- Prometheus/Grafana GPU dashboards and alerts
- optional NVIDIA NIM deployment and native NIM metrics
- comparison of Ollama/GGUF and NIM observability contracts

Status: integration path implemented; target-cluster proof required.

## Phase 5: Design-Partner Pilot

- named or responsibly anonymized enterprise workload
- agreed success criteria and data boundaries
- pilot report with measurable before/after result
- redacted validation email, reference, or approved customer quote

Status: required before enterprise traction or production-readiness claims.
