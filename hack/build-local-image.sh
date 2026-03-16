#!/usr/bin/env bash
set -euo pipefail

IMAGE_REPO="${1:-langchain-demo}"
IMAGE_TAG="${2:-0.1.0}"
BUILD_CONTEXT="${3:-}"
FULL_IMAGE="${IMAGE_REPO}:${IMAGE_TAG}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -z "${BUILD_CONTEXT}" ]]; then
  BUILD_CONTEXT="${REPO_ROOT}/${IMAGE_REPO}"
fi

if command -v nerdctl >/dev/null 2>&1; then
  echo "Building ${FULL_IMAGE} with nerdctl into containerd (k8s.io namespace)"
  sudo nerdctl --namespace k8s.io build -t "${FULL_IMAGE}" "${BUILD_CONTEXT}"
else
  echo "nerdctl not found; falling back to docker build for ${FULL_IMAGE}"
  docker build -t "${FULL_IMAGE}" "${BUILD_CONTEXT}"
fi

echo "Done: ${FULL_IMAGE}"
