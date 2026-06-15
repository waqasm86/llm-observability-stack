# Enterprise pilot proposal

## Customer and workload

- Customer/design partner: [name]
- Executive sponsor and technical owner: [roles]
- NVIDIA GPU SKU and count: [exact hardware]
- Model/runtime: [model, quantization, Ollama or NIM]
- Data classification and residency: [requirements]

## Six-week scope

1. Week 1: baseline architecture, security, and success metric sign-off.
2. Week 2: deploy SDK, collectors, dashboards, and retention.
3. Week 3: capture normal workload baseline.
4. Week 4: run load, failure, and GPU saturation scenarios.
5. Week 5: tune alerts, capacity thresholds, and runbooks.
6. Week 6: report outcomes and production rollout recommendation.

## Acceptance criteria

- At least 95% of inference requests represented in telemetry.
- TTFT, end-to-end latency, token throughput, errors, and GPU metrics visible in one workflow.
- Alert detection within [target] minutes and incident diagnosis within [target] minutes.
- Demonstrated [target]% improvement in GPU utilization or [target]% reduction in cost per request.
- No prompt or response content exported outside the approved data boundary without explicit consent.

## Commercial next step

Define pilot fee, production subscription metric, support scope, procurement owner, and decision date.
