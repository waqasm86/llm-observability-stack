#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="${NAMESPACE:-llm-observability}"
RELEASE="${RELEASE:-llm-observability-stack}"
VALUES_FILE="${VALUES_FILE:-values.enterprise-pilot-k3s.yaml}"
AUTO_DETECT_RUNTIME="${AUTO_DETECT_RUNTIME:-true}"
RUNTIME_MODE="${RUNTIME_MODE:-auto}"
RUNTIME_VALUES_FILE="${RUNTIME_VALUES_FILE:-.generated/values.runtime-detected.yaml}"

cd "${ROOT_DIR}"

args_text=" $* "
langchain_disabled=false
toolbox_disabled=false
if [[ "${args_text}" == *"langchainDemo.enabled=false"* ]]; then
  langchain_disabled=true
fi
if [[ "${args_text}" == *"pythonToolbox.enabled=false"* ]]; then
  toolbox_disabled=true
fi

check_runtime_image() {
  local pod_name="$1"
  local image="$2"

  kubectl delete pod -n "${NAMESPACE}" "${pod_name}" --ignore-not-found=true >/dev/null 2>&1 || true
  kubectl run "${pod_name}" \
    -n "${NAMESPACE}" \
    --image="${image}" \
    --image-pull-policy=Never \
    --restart=Never \
    --command -- python --version >/dev/null

  sleep 5
  local phase reason
  phase="$(kubectl get pod -n "${NAMESPACE}" "${pod_name}" -o jsonpath='{.status.phase}' 2>/dev/null || true)"
  reason="$(kubectl get pod -n "${NAMESPACE}" "${pod_name}" -o jsonpath='{.status.containerStatuses[0].state.waiting.reason}' 2>/dev/null || true)"
  kubectl delete pod -n "${NAMESPACE}" "${pod_name}" --ignore-not-found=true >/dev/null 2>&1 || true

  [[ "${phase}" == "Succeeded" && -z "${reason}" ]]
}

echo "Checking Kubernetes access"
kubectl cluster-info >/dev/null
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f - >/dev/null

values_args=(-f "${VALUES_FILE}")
if [[ "${AUTO_DETECT_RUNTIME}" == "true" ]]; then
  echo "Detecting Kubernetes runtime profile"
  ./hack/detect-runtime-profile.sh --mode "${RUNTIME_MODE}" --output "${RUNTIME_VALUES_FILE}"
  values_args+=(-f "${RUNTIME_VALUES_FILE}")
fi

missing_images=()
if [[ "${langchain_disabled}" == false ]] && ! check_runtime_image image-check-langchain langchain-demo:0.1.1; then
  missing_images+=("langchain-demo:0.1.1")
fi
if [[ "${toolbox_disabled}" == false ]] && ! check_runtime_image image-check-toolbox python-toolbox:0.2.0; then
  missing_images+=("python-toolbox:0.2.0")
fi
if (( ${#missing_images[@]} > 0 )); then
  printf 'Missing local image(s) from k3s containerd: %s\n' "${missing_images[*]}" >&2
  cat >&2 <<'EOF'
Build and import the local images first:
  ./hack/build-local-image.sh langchain-demo 0.1.1 ./langchain-demo
  ./hack/import-local-image-to-k3s.sh langchain-demo 0.1.1
  ./hack/build-local-image.sh python-toolbox 0.2.0 ./python-toolbox
  ./hack/import-local-image-to-k3s.sh python-toolbox 0.2.0

Or run a platform-only install:
  ./hack/bootstrap-enterprise-pilot-k3s.sh --set langchainDemo.enabled=false --set pythonToolbox.enabled=false
EOF
  exit 1
fi

echo "Applying Prometheus Operator CRDs"
for crd in charts/kube-prometheus-stack/charts/crds/crds/*.yaml; do
  kubectl create --save-config=false -f "${crd}" 2>/dev/null || kubectl apply --server-side -f "${crd}"
done

echo "Waiting for Prometheus Operator CRDs"
kubectl wait --for=condition=Established \
  crd/servicemonitors.monitoring.coreos.com \
  crd/prometheuses.monitoring.coreos.com \
  crd/prometheusrules.monitoring.coreos.com \
  --timeout=120s

echo "Installing enterprise-pilot profile"
helm upgrade --install "${RELEASE}" . \
  -n "${NAMESPACE}" --create-namespace \
  "${values_args[@]}" \
  --set namespace.create=false \
  --set kube-prometheus-stack.crds.enabled=false \
  "$@"

echo "Waiting for observability deployments"
kubectl rollout status deploy/kube-prometheus-stack-operator -n "${NAMESPACE}" --timeout=180s
kubectl rollout status deploy/opentelemetry-collector -n "${NAMESPACE}" --timeout=180s

echo "Current workload state"
kubectl get pods,svc -n "${NAMESPACE}"
