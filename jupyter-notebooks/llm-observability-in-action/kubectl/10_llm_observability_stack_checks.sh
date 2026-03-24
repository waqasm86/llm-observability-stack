#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmds kubectl
print_runtime_context

log_section "Namespace and release"
kctl_try get ns "${K8S_NAMESPACE}"
kctl_ns_try get all -l "app.kubernetes.io/instance=${K8S_RELEASE}" -o wide

log_section "Rollout status"
if resource_exists_ns "deploy/${LANGCHAIN_SERVICE}"; then
  kctl_ns_try rollout status "deploy/${LANGCHAIN_SERVICE}" --timeout=180s
fi

if resource_exists_ns "deploy/${OPENWEBUI_SERVICE}"; then
  kctl_ns_try rollout status "deploy/${OPENWEBUI_SERVICE}" --timeout=180s
elif resource_exists_ns "sts/${OPENWEBUI_SERVICE}"; then
  kctl_ns_try rollout status "sts/${OPENWEBUI_SERVICE}" --timeout=180s
fi

if resource_exists_ns "sts/${OLLAMA_SERVICE}"; then
  kctl_ns_try rollout status "sts/${OLLAMA_SERVICE}" --timeout=180s
elif resource_exists_ns "deploy/${OLLAMA_SERVICE}"; then
  kctl_ns_try rollout status "deploy/${OLLAMA_SERVICE}" --timeout=180s
fi

log_section "Service and endpoint checks"
for svc in "${OPENWEBUI_SERVICE}" "${OLLAMA_SERVICE}" "${LANGCHAIN_SERVICE}"; do
  kctl_ns_try get "svc/${svc}" -o wide
  kctl_ns_try get "endpoints/${svc}" -o wide
  kctl_ns_try get endpointslices.discovery.k8s.io -l "kubernetes.io/service-name=${svc}" -o wide
done

log_section "Pod readiness summary"
kctl_ns_try get pods -o custom-columns=NAME:.metadata.name,READY:.status.containerStatuses[*].ready,RESTARTS:.status.containerStatuses[*].restartCount,PHASE:.status.phase,NODE:.spec.nodeName

log_section "GPU request summary"
kctl_ns_try get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.containers[*]}{.name}{":"}{.resources.requests.nvidia\.com/gpu}{":"}{.resources.requests.nvidia\.com/gpu\.shared}{" "}{end}{"\n"}{end}'

log_section "Host-side local endpoint checks"
if command -v curl >/dev/null 2>&1; then
  if curl -fsS --max-time 5 "http://localhost:8080/" >/dev/null; then
    log_info "open-webui reachable at http://localhost:8080/"
  else
    log_warn "open-webui not reachable at http://localhost:8080/ (service may be ClusterIP or port-forward not active)."
  fi
else
  log_warn "curl not installed; skipping localhost endpoint check."
fi

log_section "Suggested smoke commands"
cat <<CMDS
kubectl -n ${K8S_NAMESPACE} port-forward svc/${OLLAMA_SERVICE} 11434:11434
curl -s http://localhost:11434/api/tags | jq

kubectl -n ${K8S_NAMESPACE} port-forward svc/${LANGCHAIN_SERVICE} 8000:8000
curl -s http://localhost:8000/healthz
CMDS
