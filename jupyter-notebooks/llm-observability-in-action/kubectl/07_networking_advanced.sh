#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmds kubectl
print_runtime_context

log_section "Gateway API resources (if CRDs exist)"
kctl_try get gatewayclass
kctl_try get gateway -A
kctl_try get httproute -A
kctl_try get tcproute -A
kctl_try get referencegrant -A

log_section "Cluster DNS and CNI components"
kctl_try -n kube-system get pods -o wide
kctl_try -n kube-system get deploy
kctl_try -n kube-system get ds

log_section "Node network topology hints"
kctl_try get nodes -o wide
kctl_try get nodes -o custom-columns=NAME:.metadata.name,PODCIDR:.spec.podCIDR,PROVIDER:.spec.providerID

log_section "Service exposure types"
kctl_ns_try get svc -o custom-columns=NAME:.metadata.name,TYPE:.spec.type,CLUSTER-IP:.spec.clusterIP,EXTERNAL-IP:.status.loadBalancer.ingress[*].ip,PORTS:.spec.ports[*].port

log_section "Optional in-cluster DNS and connectivity test"
if [[ "${APPLY_CHANGES}" == "1" ]]; then
  kctl_ns apply -f "${SCRIPT_DIR}/../manifests/networking/test-client-pod.yaml"
  kctl_ns wait --for=condition=Ready pod/k8s-net-debug --timeout=120s
  kctl_ns exec k8s-net-debug -- nslookup "${LANGCHAIN_SERVICE}.${K8S_NAMESPACE}.svc.cluster.local"
  kctl_ns exec k8s-net-debug -- nslookup "${OLLAMA_SERVICE}.${K8S_NAMESPACE}.svc.cluster.local"
  kctl_ns exec k8s-net-debug -- sh -lc "wget -qO- http://${LANGCHAIN_SERVICE}:8000/healthz || true"
  kctl_ns delete -f "${SCRIPT_DIR}/../manifests/networking/test-client-pod.yaml" --ignore-not-found=true
else
  log_info "Read-only mode: skipping temporary test pod creation. Set APPLY_CHANGES=1 to run DNS/connectivity pod test."
fi

log_section "NetworkPolicy apply helpers"
cat <<CMDS
APPLY_CHANGES=1 kubectl -n ${K8S_NAMESPACE} apply -f ${SCRIPT_DIR}/../manifests/networking/netpol.default-deny.yaml
APPLY_CHANGES=1 kubectl -n ${K8S_NAMESPACE} apply -f ${SCRIPT_DIR}/../manifests/networking/netpol.allow-dns.yaml
APPLY_CHANGES=1 kubectl -n ${K8S_NAMESPACE} apply -f ${SCRIPT_DIR}/../manifests/networking/netpol.allow-openwebui-to-langchain.yaml
CMDS
