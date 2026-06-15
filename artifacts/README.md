# Public Benchmark Artifacts

This directory stores sanitized, public benchmark artifacts.

Do not commit private customer data, secrets, kubeconfigs, raw prompts containing confidential
data, or model binaries. Every published artifact should document its hardware, software versions,
benchmark method, run count, and limitations.

The current public artifact is:

- `geforce-940m-benchmark.json`: one warmup plus three measured Gemma 3 1B IT Q4_K_M
  streaming requests on the verified local GeForce 940M edge profile.
