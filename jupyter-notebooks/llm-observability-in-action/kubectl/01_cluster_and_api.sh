#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmds kubectl
print_runtime_context

log_section "Cluster and context"
kctl_try config current-context
kctl_try config get-contexts
kctl_try cluster-info
kctl_try version

log_section "Nodes and namespaces"
kctl_try get nodes -o wide
kctl_try get namespaces --show-labels

log_section "Core API discovery"
kctl_try api-versions
kctl_try api-resources --sort-by=name
kctl_try api-resources --verbs=list --namespaced=true -o name | sort | sed -n '1,120p'
kctl_try api-resources --verbs=list --namespaced=false -o name | sort

log_section "Resource schema lookups (kubectl explain)"
kctl_try explain pod.spec
kctl_try explain deployment.spec.strategy
kctl_try explain service.spec
kctl_try explain ingress.spec.rules

log_section "Recent events across all namespaces"
kctl_try get events -A --sort-by=.metadata.creationTimestamp | tail -n 80
