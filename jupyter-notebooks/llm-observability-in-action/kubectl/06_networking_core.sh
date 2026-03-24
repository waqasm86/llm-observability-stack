#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmds kubectl
print_runtime_context

log_section "Service inventory"
kctl_ns_try get svc -o wide

log_section "Endpoints and EndpointSlices"
kctl_ns_try get endpoints -o wide
kctl_ns_try get endpointslices.discovery.k8s.io -o wide

log_section "Ingress and NetworkPolicy"
kctl_ns_try get ingress -o wide
kctl_ns_try get networkpolicy -o wide

log_section "llm-observability service deep dive"
for svc in "${OPENWEBUI_SERVICE}" "${OLLAMA_SERVICE}" "${LANGCHAIN_SERVICE}"; do
  kctl_ns_try get "svc/${svc}" -o wide
  kctl_ns_try describe "svc/${svc}"
  kctl_ns_try get "endpoints/${svc}" -o wide
  kctl_ns_try get endpointslices.discovery.k8s.io -l "kubernetes.io/service-name=${svc}" -o wide
done

log_section "DNS names"
for svc in "${OPENWEBUI_SERVICE}" "${OLLAMA_SERVICE}" "${LANGCHAIN_SERVICE}"; do
  printf '%s\n' "${svc}.${K8S_NAMESPACE}.svc.cluster.local"
done

log_section "Port-forward helpers"
cat <<CMDS
kubectl -n ${K8S_NAMESPACE} port-forward svc/${OPENWEBUI_SERVICE} 8080:8080
kubectl -n ${K8S_NAMESPACE} port-forward svc/${OLLAMA_SERVICE} 11434:11434
kubectl -n ${K8S_NAMESPACE} port-forward svc/${LANGCHAIN_SERVICE} 8000:8000
CMDS
