#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmds kubectl
print_runtime_context

log_section "Storage classes"
kctl_try get storageclass

log_section "Persistent volumes and claims"
kctl_try get pv
kctl_ns_try get pvc -o wide

log_section "PVC details"
while IFS= read -r pvc_name; do
  [[ -z "${pvc_name}" ]] && continue
  kctl_ns_try describe "pvc/${pvc_name}"
done < <(kctl_ns_capture get pvc -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)

log_section "Pod volume mount summary"
kctl_ns_try get pod -o go-template='{{range .items}}{{.metadata.name}}{{"\t"}}{{range .spec.volumes}}{{.name}}{{":"}}{{if .persistentVolumeClaim}}pvc/{{.persistentVolumeClaim.claimName}}{{else if .configMap}}cm/{{.configMap.name}}{{else if .secret}}secret/{{.secret.secretName}}{{else if .emptyDir}}emptyDir{{else}}other{{end}}{{" "}}{{end}}{{"\n"}}{{end}}'

log_section "Volume attachment view"
kctl_try get volumeattachments.storage.k8s.io

log_section "Storage diagnostics examples"
cat <<CMDS
kubectl -n ${K8S_NAMESPACE} describe pvc <claim-name>
kubectl -n ${K8S_NAMESPACE} exec -it <pod-name> -- df -h
kubectl get pv <pv-name> -o yaml
CMDS
