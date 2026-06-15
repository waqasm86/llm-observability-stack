# Single-node k3s and GeForce 940M

On this Xubuntu host, the k3s server process already runs the control plane, kubelet, containerd,
and workloads. The same Kubernetes Node is therefore both control-plane and worker. Do not start a
second k3s agent on the same operating-system instance: duplicate kubelet, CNI, port, device-plugin,
and host-path ownership would make that topology unreliable.

## Prepare the combined node

```bash
./hack/prepare-single-node-k3s.sh
./hack/install-nvidia-device-plugin.sh
kubectl get nodes --show-labels
```

The scripts retain the existing control-plane role and add worker, GPU-present, and model-host
labels. The device plugin must expose one `nvidia.com/gpu` before Ollama is installed.

## Deploy the exact local GGUF model

```bash
helm upgrade --install llm-observability-stack . \
  --namespace llm-observability --create-namespace \
  -f values.geforce-940m-k3s.yaml

kubectl rollout status deployment/ollama -n llm-observability --timeout=10m
kubectl port-forward -n llm-observability service/ollama 11434:11434
```

In another terminal:

```bash
curl -s http://127.0.0.1:11434/api/tags | jq
curl -s http://127.0.0.1:11434/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"model":"gemma3-1b-it-gguf-local","prompt":"Reply with one short sentence.","stream":false}' | jq
kubectl logs -n llm-observability deployment/ollama | grep -Ei 'cuda|gpu|offload|memory'
```

The profile reads `Modelfile.gemma-3-1b-it-gguf` directly and mounts the verified host directory.
It intentionally starts only Ollama. Enable the API, Open WebUI, and monitoring after this GPU
inference baseline is healthy.

Verified on June 15, 2026:

- k3s node role: `control-plane,worker`
- device resource: one allocatable `nvidia.com/gpu`
- model: `gemma3-1b-it-gguf-local:latest`, 806 MB
- Ollama detection: CUDA compute 5.0, NVIDIA GeForce 940M, approximately 969 MiB free VRAM
- observed inference: 6.1 seconds, up to 52% GPU utilization and 554 MiB VRAM

Run `./hack/test-geforce-940m-inference.sh` to repeat the smoke test.

## Separate physical worker

A real two-node topology requires another machine or VM with its own hostname, IP, filesystems, and
GPU access. Run the k3s agent there with the server URL and node token, copy or remotely mount the
GGUF directory, then label that node with `nvidia.com/gpu.present=true` and
`llm-observability.io/model-host=true`.
