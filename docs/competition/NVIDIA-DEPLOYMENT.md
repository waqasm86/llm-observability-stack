# NVIDIA deployment profile

The application chart assumes the NVIDIA runtime and allocatable nvidia.com/gpu resources already
exist. For a supported cluster, use NVIDIA GPU Operator to manage the driver/runtime/device plugin
and enable DCGM Exporter. Confirm the operator version supports the Kubernetes and driver versions
selected for the demo.

Deployment order:

1. Provision a supported NVIDIA GPU node and validate nvidia-smi.
2. Install GPU Operator and verify nvidia.com/gpu capacity and DCGM metrics.
3. Build the monitoring chart dependencies and install monitoring.
4. Create LangSmith and Open WebUI Secrets outside Git.
5. Install the application with values.competition-nvidia.example.yaml plus a private values file.
6. Verify Prometheus targets, Grafana persistence, alerts, and the benchmark path.

NIM mode is optional. When used, configure monitoring.nim.serviceMonitor to match the NIM Service
labels and its /v1/metrics port. Keep Ollama mode as a portable demonstration path, not as evidence
that the project itself is an NVIDIA inference runtime.
