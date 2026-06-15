# Two-minute demo runbook

## Preflight

1. Run hack/competition-validate.sh with strict GPU validation on the target NVIDIA cluster.
2. Confirm Prometheus targets are healthy and both custom dashboards are loaded.
3. Warm the model, then reset the Grafana time range to the last 15 minutes.
4. Prepare one known-good request and one controlled failure.

## Timeline

- **0:00-0:15**: State the enterprise problem and identify the deployed NVIDIA GPU and model.
- **0:15-0:35**: Send a real streaming prompt through Open WebUI or the API.
- **0:35-0:55**: Show the trace and correlated request ID in the application telemetry.
- **0:55-1:20**: Show TTFT, ITL, token throughput, error rate, GPU utilization, memory, power, and temperature.
- **1:20-1:40**: Trigger or show a recorded service/GPU alert and the linked runbook.
- **1:40-1:55**: Run the benchmark result panel and state measured before/after improvement.
- **1:55-2:00**: State the customer pilot ask.

Record a backup video. Do not depend on model downloads, chart installs, or public internet during judging.
