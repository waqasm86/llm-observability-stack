# Python Kubernetes scripts

These scripts use the official Kubernetes Python client and are focused on your local `llm-observability` namespace.

## Install

```bash
/usr/local/bin/python3.11 -m venv .venv
source .venv/bin/activate
pip install -r python/requirements.txt
```

## Scripts

1. `01_namespace_inventory.py`
- Full inventory across workloads, services, endpoints, config, and storage.

2. `02_service_path_inspector.py`
- Service flow tracing from selectors to pods/endpoints and ingress/http route references.

3. `03_workload_health.py`
- Rollout and availability health checks; exits non-zero if issues are detected.

4. `04_networking_report.py`
- Networking graph-style report of services, selectors, endpoints, and DNS names.

5. `05_watch_events.py`
- Live event streaming in namespace for troubleshooting.

## Examples

```bash
/usr/local/bin/python3.11 python/01_namespace_inventory.py --namespace llm-observability
/usr/local/bin/python3.11 python/02_service_path_inspector.py --namespace llm-observability --service ollama
/usr/local/bin/python3.11 python/03_workload_health.py --namespace llm-observability
/usr/local/bin/python3.11 python/04_networking_report.py --namespace llm-observability --json
/usr/local/bin/python3.11 python/05_watch_events.py --namespace llm-observability --timeout 180
```
