# hack Scripts

This directory contains the local image workflow helpers for `llm-observability-stack`.

## Scripts

- `build-local-image.sh`
  - builds a local image for a component directory
  - prefers `nerdctl --namespace k8s.io`
  - falls back to Docker when `nerdctl` is unavailable

- `import-local-image-to-k3s.sh`
  - saves a local image to a temporary tarball
  - imports that image into k3s containerd
  - skips import when the image already exists in containerd

## Typical Usage

Build/import `langchain-demo`:

```bash
./hack/build-local-image.sh langchain-demo 0.1.1 ./langchain-demo
./hack/import-local-image-to-k3s.sh langchain-demo 0.1.1
```

Build/import `python-toolbox`:

```bash
./hack/build-local-image.sh python-toolbox 0.2.0 ./python-toolbox
./hack/import-local-image-to-k3s.sh python-toolbox 0.2.0
```

## When To Use These Scripts

- after changing `langchain-demo/app.py`
- after changing scripts or dependencies in `python-toolbox/`
- when refreshing local image tags used by the chart

## After Import

Restart the matching Kubernetes workload:

```bash
kubectl rollout restart deploy/langchain-demo -n llm-observability
kubectl rollout restart deploy/python-toolbox -n llm-observability
```

Then verify:

```bash
kubectl rollout status deploy/langchain-demo -n llm-observability
kubectl rollout status deploy/python-toolbox -n llm-observability
sudo k3s ctr images ls | grep -E 'langchain-demo|python-toolbox'
```
