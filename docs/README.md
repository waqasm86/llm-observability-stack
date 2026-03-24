# Documentation Index

This directory contains the long-form documentation for `llm-observability-stack`. The intent is to keep the top-level [README.md](../README.md) fast to scan while preserving deeper operational, architectural, and workflow guidance here.

Current local profile notes:

- `open-webui` is the main browser entrypoint
- `ollama` and `langchain-demo` are internal `ClusterIP` services by default
- `pythonToolbox.enabled: true`
- `langsmithDashboardSeeder.enabled: false`

## Start Here

1. [QUICKSTART.md](QUICKSTART.md)
2. [ARCHITECTURE.md](ARCHITECTURE.md)
3. [OPERATIONS-RUNBOOK.md](OPERATIONS-RUNBOOK.md)
4. [NOTEBOOKS-GUIDE.md](NOTEBOOKS-GUIDE.md)
5. [PROJECT-DOCUMENTATION.md](PROJECT-DOCUMENTATION.md)

## Core Guides

- [QUICKSTART.md](QUICKSTART.md)
  - Fast local setup for k3s, values files, image build/import, install, and first validation.
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

## Supporting Script Docs

- [scripts/README.md](scripts/README.md)
  - Inventory of standalone helper scripts in `docs/scripts/`.

## Related Component Docs

- [../langchain-demo/README.md](../langchain-demo/README.md)
- [../python-toolbox/README.md](../python-toolbox/README.md)
- [../hack/README.md](../hack/README.md)
- [../jupyter-notebooks/README.md](../jupyter-notebooks/README.md)
- [../jupyter-notebooks/llm-observability-in-action/README.md](../jupyter-notebooks/llm-observability-in-action/README.md)
