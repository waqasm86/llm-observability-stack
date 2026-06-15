# Documentation Index

This directory contains the long-form documentation for `llm-observability-stack`. The intent is to keep the top-level [README.md](../README.md) fast to scan while preserving deeper operational, architectural, and workflow guidance here.

This documentation is now organized around EdgeLLM Observability: private LLM deployment and
observability on NVIDIA-powered Linux edge devices using k3s, Helm, GGUF/Ollama,
LangChain/LangSmith-compatible tracing, Prometheus/Grafana, and NVIDIA GPU metrics. The repository
is a pilot-ready, production-oriented reference architecture, not a claim of universal laptop or
customer production readiness.

Current local-profile reference:

- See [CONFIG-PROFILES.md](CONFIG-PROFILES.md) for the canonical defaults and local-example overrides.

## Start Here

1. [QUICKSTART.md](QUICKSTART.md)
2. [CONFIG-PROFILES.md](CONFIG-PROFILES.md)
3. [ARCHITECTURE.md](ARCHITECTURE.md)
4. [OPERATIONS-RUNBOOK.md](OPERATIONS-RUNBOOK.md)
5. [NOTEBOOKS-GUIDE.md](NOTEBOOKS-GUIDE.md)
6. [PROJECT-DOCUMENTATION.md](PROJECT-DOCUMENTATION.md)
7. [competition/README.md](competition/README.md)

## Core Guides

- [QUICKSTART.md](QUICKSTART.md)
  - Fast local setup for k3s, values files, image build/import, install, and first validation.
- [CONFIG-PROFILES.md](CONFIG-PROFILES.md)
  - Canonical comparison of git-tracked defaults, local example values, and private local overrides.
- [ARCHITECTURE.md](ARCHITECTURE.md)
  - Component ownership, request paths, service exposure, and configuration boundaries.
- [OPERATIONS-RUNBOOK.md](OPERATIONS-RUNBOOK.md)
  - Day-0 and day-1 tasks: deploy, verify, port-forward, rebuild images, debug, and clean up.
- [NOTEBOOKS-GUIDE.md](NOTEBOOKS-GUIDE.md)
  - Walkthrough of notebooks `01` through `10`, their prerequisites, and common execution pitfalls.
- [PROJECT-DOCUMENTATION.md](PROJECT-DOCUMENTATION.md)
  - Full repository documentation, component walkthroughs, and deployment model.
- [PROJECT-ANALYSIS.md](PROJECT-ANALYSIS.md)
  - Current-state summary and hardening priorities.

## Kubernetes and Automation Guides

- [KUBERNETES-NETWORKING.md](KUBERNETES-NETWORKING.md)
  - Service, EndpointSlice, DNS, ServiceLB, and traffic-path documentation for this stack.
- [KUBECTL-COMMAND-REFERENCE.md](KUBECTL-COMMAND-REFERENCE.md)
  - High-signal `kubectl` command catalog for local operations.
- [PYTHON-KUBERNETES-AUTOMATION.md](PYTHON-KUBERNETES-AUTOMATION.md)
  - Kubernetes Python client usage patterns and script-driven inspection.

## Git and Publishing

- [GITHUB-PUBLISHING.md](GITHUB-PUBLISHING.md)
  - Remote setup, safe publishing workflow, and repo hygiene guidance.

## NVIDIA Inception and Pilot Materials

- [competition/README.md](competition/README.md)
  - Product positioning, evidence, NVIDIA alignment, and remaining proof targets.
- [competition/EDGE-VALIDATION-ROADMAP.md](competition/EDGE-VALIDATION-ROADMAP.md)
  - Hardware and pilot validation phases from GeForce 940M to RTX, DCGM/NIM, and design partners.
- [competition/EDGE-BUSINESS-MODEL.md](competition/EDGE-BUSINESS-MODEL.md)
  - Open-source, enterprise pilot, and OEM/SI commercial paths.
- [competition/LENOVO-OEM-ANGLE.md](competition/LENOVO-OEM-ANGLE.md)
  - Future OEM validation and sponsorship path without implying current endorsement.

## Suggested Reading Paths

- First deploy:
  - [QUICKSTART.md](QUICKSTART.md)
  - [CONFIG-PROFILES.md](CONFIG-PROFILES.md)
  - [OPERATIONS-RUNBOOK.md](OPERATIONS-RUNBOOK.md)
- Notebook-focused:
  - [NOTEBOOKS-GUIDE.md](NOTEBOOKS-GUIDE.md)
  - [../jupyter-notebooks/CATALOG.md](../jupyter-notebooks/CATALOG.md)
  - [../jupyter-notebooks/README.md](../jupyter-notebooks/README.md)
- Contributor/operator:
  - [../CONTRIBUTING.md](../CONTRIBUTING.md)
  - [KUBECTL-COMMAND-REFERENCE.md](KUBECTL-COMMAND-REFERENCE.md)
  - [PYTHON-KUBERNETES-AUTOMATION.md](PYTHON-KUBERNETES-AUTOMATION.md)

## Supporting Script Docs

- [scripts/README.md](scripts/README.md)
  - Inventory of standalone helper scripts in `docs/scripts/`.

## Related Component Docs

- [../langchain-demo/README.md](../langchain-demo/README.md)
- [../python-toolbox/README.md](../python-toolbox/README.md)
- [../hack/README.md](../hack/README.md)
- [../jupyter-notebooks/README.md](../jupyter-notebooks/README.md)
- [../jupyter-notebooks/llm-observability-in-action/README.md](../jupyter-notebooks/llm-observability-in-action/README.md)
