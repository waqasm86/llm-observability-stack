# Verified local GPU results

Captured on June 15, 2026 from the Xubuntu 24.04 single-node k3s deployment.

## Environment

- Node: `waqasm86-thinkpad-t450s`
- Kubernetes role: combined `control-plane,worker`
- k3s: v1.35.5+k3s1
- GPU: NVIDIA GeForce 940M, 1 GiB VRAM, CUDA compute capability 5.0
- Driver: 580.95.05
- NVIDIA device plugin: 0.18.1
- Ollama: 0.17.7
- Model: Gemma 3 1B IT Q4_K_M, 806,058,272 bytes
- Model SHA-256: `8270790f3ab69fdfe860b7b64008d9a19986d8df7e407bb018184caa08798ebd`

## Inference evidence

Ollama detected the GPU through CUDA and reported approximately 968.8 MiB available VRAM.
A live one-sentence inference completed in 6.1 seconds. Concurrent `nvidia-smi` sampling observed:

- peak GPU utilization: 52%
- loaded-model VRAM: 554 MiB
- observed temperature range: 53-58 degrees Celsius

## API benchmark

Method: one warmup followed by three streaming `/api/generate` requests, concurrency one.

| Metric | Result |
|---|---:|
| TTFT p50 | 0.377 s |
| TTFT p95 | 0.381 s |
| End-to-end p50 | 6.782 s |
| End-to-end p95 | 6.972 s |
| Mean generated throughput | 11.694 tokens/s |
| Prompt tokens per run | 17 |
| Generated tokens per run | 71 |

These figures demonstrate the low-cost local profile. They are not a substitute for enterprise
load, concurrency, reliability, or modern NVIDIA data-center GPU benchmarks.
