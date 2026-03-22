# python-toolbox

A small in-cluster Python toolbox for Kubernetes networking checks.

Status in the default local profile:

- `pythonToolbox.enabled: false` (enable only when needed)
- continuous LangSmith seeder jobs are disabled by default

Included examples:
- `service_dns_check.py`
- `ollama_smoke.py`
- `redis_ping.py`
- `langsmith_healthcheck.py`
- `langsmith_inference_traces.py` (seed LangSmith Monitoring charts with traced inference runs)
- `langsmith_dashboard_seed_every_5m.py` (continuous chart seeding every 5 minutes)

The image is intentionally small and does not include JupyterLab.
Use `kubectl exec` into the pod and run scripts directly.

Quick shell access:

```bash
kubectl exec -it -n llm-observability deploy/python-toolbox -- bash
```

Seed LangSmith chart data:

```bash
kubectl exec -it -n llm-observability deploy/python-toolbox -- \
  python /workspace/examples/langsmith_inference_traces.py
```

Run continuous 5-minute chart seeding:

```bash
kubectl exec -it -n llm-observability deploy/python-toolbox -- \
  env OBS_CALL_COUNT_PER_CYCLE=4 OBS_INTERVAL_SECONDS=300 \
  python /workspace/examples/langsmith_dashboard_seed_every_5m.py
```
