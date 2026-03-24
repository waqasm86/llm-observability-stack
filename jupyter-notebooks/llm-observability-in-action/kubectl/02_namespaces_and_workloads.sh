#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmds kubectl
print_runtime_context

log_section "Namespace workloads overview"
kctl_ns_try get deployment,statefulset,daemonset,replicaset,pod,job,cronjob -o wide

log_section "Deployments"
kctl_ns_try get deploy -o custom-columns=NAME:.metadata.name,DESIRED:.spec.replicas,UPDATED:.status.updatedReplicas,AVAILABLE:.status.availableReplicas,AGE:.metadata.creationTimestamp

log_section "StatefulSets"
kctl_ns_try get sts -o custom-columns=NAME:.metadata.name,DESIRED:.spec.replicas,READY:.status.readyReplicas,SERVICE:.spec.serviceName,AGE:.metadata.creationTimestamp

log_section "DaemonSets"
kctl_ns_try get ds -o custom-columns=NAME:.metadata.name,DESIRED:.status.desiredNumberScheduled,READY:.status.numberReady,AVAILABLE:.status.numberAvailable,AGE:.metadata.creationTimestamp

log_section "Rollout status checks"
while IFS= read -r deploy_name; do
  [[ -z "${deploy_name}" ]] && continue
  kctl_ns_try rollout status "deploy/${deploy_name}" --timeout=120s
done < <(kctl_ns_capture get deploy -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)

while IFS= read -r sts_name; do
  [[ -z "${sts_name}" ]] && continue
  kctl_ns_try rollout status "sts/${sts_name}" --timeout=120s
done < <(kctl_ns_capture get sts -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)

log_section "llm-observability key workloads"
if resource_exists_ns "deploy/${LANGCHAIN_SERVICE}"; then
  kctl_ns_try get "deploy/${LANGCHAIN_SERVICE}" -o wide
  kctl_ns_try describe "deploy/${LANGCHAIN_SERVICE}"
fi

if resource_exists_ns "deploy/${OPENWEBUI_SERVICE}"; then
  kctl_ns_try get "deploy/${OPENWEBUI_SERVICE}" -o wide
  kctl_ns_try describe "deploy/${OPENWEBUI_SERVICE}"
elif resource_exists_ns "sts/${OPENWEBUI_SERVICE}"; then
  kctl_ns_try get "sts/${OPENWEBUI_SERVICE}" -o wide
  kctl_ns_try describe "sts/${OPENWEBUI_SERVICE}"
fi

if resource_exists_ns "sts/${OLLAMA_SERVICE}"; then
  kctl_ns_try get "sts/${OLLAMA_SERVICE}" -o wide
  kctl_ns_try describe "sts/${OLLAMA_SERVICE}"
elif resource_exists_ns "deploy/${OLLAMA_SERVICE}"; then
  kctl_ns_try get "deploy/${OLLAMA_SERVICE}" -o wide
  kctl_ns_try describe "deploy/${OLLAMA_SERVICE}"
fi

log_section "Controller selectors"
kctl_ns_try get deploy,sts,ds -o go-template='{{range .items}}{{printf "%s/%s\tselector=%v\n" .kind .metadata.name .spec.selector.matchLabels}}{{end}}'
