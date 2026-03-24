# Notebook Guide

This guide explains how the notebook suite in `jupyter-notebooks/` is intended to be used on a local k3s workstation. The notebooks are written for iterative hands-on use, not for unattended CI. Several cells assume a running cluster, live services, and host access to internal APIs through `kubectl port-forward`.

## Core Sequence

1. `01-environment-smoke-test.ipynb`
   - Confirms the Python 3.11 kernel, core CLI tools, cluster health, GPU visibility, and active Helm values.
   - Use this first whenever the machine has rebooted or the cluster was recreated.
2. `02-ollama-api-basics.ipynb`
   - Exercises Ollama directly through its HTTP API.
   - Requires `kubectl port-forward -n llm-observability svc/ollama 11434:11434`.
3. `03-langchain-proxy-deep-dive.ipynb`
   - Validates the local FastAPI proxy and compares direct-vs-proxy request behavior.
   - Requires `kubectl port-forward -n llm-observability svc/langchain-demo 8000:8000`.
4. `04-langsmith-tracing-setup.ipynb`
   - Confirms LangSmith credentials, pushes traced inference traffic, and queries recorded runs.
   - Requires the LangSmith environment variables in the notebook kernel plus the same port-forwards used by `02` and `03`.
5. `05-open-webui-end-to-end.ipynb`
   - Walks through the browser path from Open WebUI through the proxy to Ollama and then back to LangSmith.
   - Requires a browser session in Open WebUI and manual prompt submission.
6. `06-custom-modelfile-workflow.ipynb`
   - Focuses on Modelfile customization, optional model creation, and comparison benchmarking.
   - Does not create custom models unless you explicitly enable the relevant cells.
7. `07-python-toolbox-diagnostics.ipynb`
   - Uses the in-cluster `python-toolbox` deployment for diagnostics, DNS checks, and script execution.
   - Assumes `pythonToolbox.enabled: true` in the active release or local values profile.
8. `08-troubleshooting-etcd-simulations.ipynb`
   - Covers troubleshooting drills, rendered-manifest inspection, and operational failure simulation.
   - Best used after you understand the happy-path stack behavior from notebooks `01` through `07`.
9. `09-k3s-networking-deep-dive.ipynb`
   - Uses the Kubernetes Python client to inspect Services, EndpointSlices, DNS, `svclb-*` ServiceLB pods, and in-cluster connectivity.
   - Good for understanding how your local k3s node is wiring the stack together.
10. `10-k3s-architecture-diagrams.ipynb`
   - Captures architecture-oriented visualizations and diagram-focused material for presentation or walkthrough use.
   - Treat this as a communication notebook rather than a primary smoke test.

## Supporting Example Notebooks

The repository also contains `llm-observability-stack-example-*.ipynb` notebooks. These are better treated as snapshots or focused demonstrations than as the main tutorial path. They often contain exploratory outputs that are useful locally but should not be treated as the source of truth for the current deployment flow.

## Shared Prerequisites

- `kubectl` must point at the intended local k3s cluster.
- The Helm release `llm-observability-stack` should be installed in the `llm-observability` namespace.
- `pythonToolbox.enabled` should remain `true` for the local profile.
- Python 3.11 and the `python311` kernelspec should be available.
- The local machine should have enough RAM and GPU headroom for Ollama inference.

Recommended preflight:

```bash
kubectl get all -n llm-observability
kubectl get svc -n llm-observability
kubectl get endpointslices -n llm-observability
```

## Port-Forward Matrix

Use separate terminals for these when working from the host:

```bash
kubectl port-forward -n llm-observability svc/ollama 11434:11434
kubectl port-forward -n llm-observability svc/langchain-demo 8000:8000
kubectl port-forward -n llm-observability svc/open-webui 8080:8080
```

Typical dependency map:

- `02` needs Ollama on `localhost:11434`
- `03` needs the proxy on `localhost:8000`
- `04` needs both `localhost:8000` and `localhost:11434`
- `05` needs browser access to Open WebUI plus LangSmith environment variables if tracing is being validated
- `06` usually needs Ollama on `localhost:11434`
- `07` primarily uses the in-cluster toolbox, but some optional checks use `localhost:8000`
- `09` mostly uses the Kubernetes API directly and only shells into `python-toolbox` for in-cluster probes

## Execution Guidance

- Re-run notebook `01` after cluster restarts or Helm upgrades.
- Treat saved outputs as historical context only; re-execution is the authoritative check.
- If a notebook prints a port-forward command, open it in another terminal and rerun the affected cell.
- Keep LangSmith keys in the environment, not in notebook source.
- Prefer the local values file for machine-specific overrides and keep it out of git.

## Common Failure Modes

- `Connection refused` to `localhost:11434` or `localhost:8000`
  - Missing port-forward or the backing pod is not ready.
- `No running python-toolbox pod found`
  - The release is disabled or the deployment needs a restart.
- Empty LangSmith result tables
  - Credentials are missing, tracing is disabled, or the project name does not match the release configuration.
- Networking notebook probe parse failures
  - Re-run after updating to the current notebook version; the probe cell now tolerates both JSON and Python-literal exec output.

## Publication Guidance

Notebook outputs are useful while developing locally, but they can become stale quickly and may reveal cluster-specific details. Before publishing broadly, clear outputs and do not commit `.ipynb_checkpoints/` content.
