#!/usr/bin/env bash
set -euo pipefail

IMAGE_REPO="${1:-langchain-demo}"
IMAGE_TAG="${2:-0.1.0}"
FULL_IMAGE="${IMAGE_REPO}:${IMAGE_TAG}"
TMP_TAR="$(mktemp /tmp/local-image.XXXXXX.tar)"
trap 'rm -f "${TMP_TAR}"' EXIT

if command -v nerdctl >/dev/null 2>&1; then
  echo "Checking whether ${FULL_IMAGE} already exists in k3s containerd"
  if sudo nerdctl --namespace k8s.io images | awk '{print $1":"$2}' | grep -qx "${FULL_IMAGE}"; then
    echo "Image already present in containerd: ${FULL_IMAGE}"
    exit 0
  fi
fi

echo "Saving ${FULL_IMAGE} to ${TMP_TAR}"
if command -v nerdctl >/dev/null 2>&1; then
  sudo nerdctl --namespace k8s.io save -o "${TMP_TAR}" "${FULL_IMAGE}"
else
  docker save -o "${TMP_TAR}" "${FULL_IMAGE}"
fi

echo "Importing ${FULL_IMAGE} into k3s containerd"
sudo k3s ctr images import "${TMP_TAR}"

echo "Imported: ${FULL_IMAGE}"
