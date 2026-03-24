#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmds kubectl
print_runtime_context

log_section "Pod inventory"
kctl_ns_try get pods -o wide
kctl_ns_try get pods -o custom-columns=NAME:.metadata.name,PHASE:.status.phase,READY:.status.containerStatuses[*].ready,RESTARTS:.status.containerStatuses[*].restartCount,NODE:.spec.nodeName

log_section "Non-running pods"
non_running="$(kctl_ns_capture get pods --field-selector=status.phase!=Running -o name 2>/dev/null || true)"
if [[ -z "${non_running}" ]]; then
  log_info "All pods are in Running phase (or no pods found)."
else
  while IFS= read -r pod_ref; do
    [[ -z "${pod_ref}" ]] && continue
    kctl_ns_try describe "${pod_ref}"
  done <<< "${non_running}"
fi

log_section "Recent logs (key workloads)"
kctl_ns_try logs "deploy/${LANGCHAIN_SERVICE}" --all-containers=true --tail=120
if resource_exists_ns "deploy/${OPENWEBUI_SERVICE}"; then
  kctl_ns_try logs "deploy/${OPENWEBUI_SERVICE}" --all-containers=true --tail=120
elif resource_exists_ns "sts/${OPENWEBUI_SERVICE}"; then
  kctl_ns_try logs "sts/${OPENWEBUI_SERVICE}" --all-containers=true --tail=120
fi

if resource_exists_ns "sts/${OLLAMA_SERVICE}"; then
  kctl_ns_try logs "sts/${OLLAMA_SERVICE}" --all-containers=true --tail=120
elif resource_exists_ns "deploy/${OLLAMA_SERVICE}"; then
  kctl_ns_try logs "deploy/${OLLAMA_SERVICE}" --all-containers=true --tail=120
fi

log_section "Resource usage (metrics-server dependent)"
kctl_ns_try top pods
kctl_try top nodes

log_section "Namespace events"
kctl_ns_try get events --sort-by=.metadata.creationTimestamp | tail -n 120

log_section "Interactive debug examples"
cat <<CMDS
kubectl -n ${K8S_NAMESPACE} describe pod <pod-name>
kubectl -n ${K8S_NAMESPACE} logs <pod-name> --all-containers --tail=200
kubectl -n ${K8S_NAMESPACE} exec -it <pod-name> -- sh
kubectl -n ${K8S_NAMESPACE} debug -it <pod-name> --image=busybox:1.36 --target=<container-name>
CMDS
