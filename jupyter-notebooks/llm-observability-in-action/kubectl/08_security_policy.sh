#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmds kubectl
print_runtime_context

log_section "Namespace labels and pod security admission"
kctl_try get ns "${K8S_NAMESPACE}" --show-labels

log_section "Service accounts"
kctl_ns_try get serviceaccount -o wide

log_section "RBAC"
kctl_ns_try get role,rolebinding -o wide
kctl_try get clusterrole,clusterrolebinding -o wide

log_section "Auth checks"
kctl_try auth can-i get pods -n "${K8S_NAMESPACE}"
kctl_try auth can-i list secrets -n "${K8S_NAMESPACE}"
kctl_try auth can-i --as="system:serviceaccount:${K8S_NAMESPACE}:default" get pods -n "${K8S_NAMESPACE}"
kctl_try auth can-i --as="system:serviceaccount:${K8S_NAMESPACE}:default" list secrets -n "${K8S_NAMESPACE}"

log_section "Pod security contexts"
kctl_ns_try get pods -o custom-columns=NAME:.metadata.name,SA:.spec.serviceAccountName,RUN-AS-NON-ROOT:.spec.securityContext.runAsNonRoot,HOST-NETWORK:.spec.hostNetwork

log_section "Secret types"
kctl_ns_try get secrets -o custom-columns=NAME:.metadata.name,TYPE:.type

log_section "Network policies"
kctl_ns_try get networkpolicy -o yaml
