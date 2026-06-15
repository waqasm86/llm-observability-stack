# Evidence checklist

- Git commit SHA and tagged release used for the demo
- Kubernetes, Helm, GPU Operator, driver, CUDA, DCGM, and runtime versions
- Exact NVIDIA GPU SKU, count, memory, and cloud/host pricing assumption
- Model name, revision, quantization, context length, and serving parameters
- Benchmark prompt set, warmups, run count, concurrency, and raw JSON
- TTFT p50/p95, latency p50/p95, tokens/second, error rate, requests/second
- GPU utilization, framebuffer memory, power, temperature, and Tensor Core activity
- Baseline comparison and cost calculation method
- Grafana screenshots with timestamps and visible units
- Alert drill result and measured detection/diagnosis time
- Customer permission for names, logos, quotes, and metrics
- Pilot/LOI/customer reference document
- Security architecture and data-flow review
- Two-minute primary demo and offline backup

Store private customer evidence outside the public repository. Keep a sanitized evidence index here.
