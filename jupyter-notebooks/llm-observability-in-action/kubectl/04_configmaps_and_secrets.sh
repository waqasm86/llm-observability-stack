#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmds kubectl
print_runtime_context

log_section "ConfigMaps"
kctl_ns_try get configmap -o wide
kctl_ns_try describe configmap ollama-local-modelfile
kctl_ns_try describe configmap langchain-demo-app

log_section "Secrets"
kctl_ns_try get secret -o custom-columns=NAME:.metadata.name,TYPE:.type,AGE:.metadata.creationTimestamp

log_section "Secret key inventory (values are never printed)"
kctl_ns_try get secret -o go-template='{{range .items}}{{printf "%s\t" .metadata.name}}{{range $k,$v := .data}}{{printf "%s " $k}}{{end}}{{"\n"}}{{end}}'

log_section "Chart-relevant secret checks"
kctl_ns_try describe secret langsmith-secret
kctl_ns_try describe secret open-webui-secrets

log_section "Secret wiring helper commands"
cat <<CMDS
# Generate secret manifests without applying:
kubectl -n ${K8S_NAMESPACE} create secret generic langsmith-secret \
  --from-literal=LANGSMITH_API_KEY=replace-me \
  --dry-run=client -o yaml

kubectl -n ${K8S_NAMESPACE} create secret generic open-webui-secrets \
  --from-literal=WEBUI_SECRET_KEY=replace-with-32-plus-char-value \
  --dry-run=client -o yaml
CMDS

if [[ "${APPLY_CHANGES}" == "1" ]]; then
  log_section "Mutating demo: apply sample runtime ConfigMap"
  kctl_ns apply -f "${SCRIPT_DIR}/../manifests/workloads/cm.runtime-notes.yaml"
else
  log_info "Read-only mode: skipping mutating apply examples. Set APPLY_CHANGES=1 to enable."
fi
