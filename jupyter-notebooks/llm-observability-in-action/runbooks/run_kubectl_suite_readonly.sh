#!/usr/bin/env bash
set -euo pipefail

RUNBOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT_DIR="$(cd "${RUNBOOK_DIR}/.." && pwd -P)"

if [[ -f "${ROOT_DIR}/config.env" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/config.env"
fi

export APPLY_CHANGES=0

for script in \
  "${ROOT_DIR}/kubectl/01_cluster_and_api.sh" \
  "${ROOT_DIR}/kubectl/02_namespaces_and_workloads.sh" \
  "${ROOT_DIR}/kubectl/03_pods_lifecycle_debug.sh" \
  "${ROOT_DIR}/kubectl/04_configmaps_and_secrets.sh" \
  "${ROOT_DIR}/kubectl/05_storage_and_volumes.sh" \
  "${ROOT_DIR}/kubectl/06_networking_core.sh" \
  "${ROOT_DIR}/kubectl/07_networking_advanced.sh" \
  "${ROOT_DIR}/kubectl/08_security_policy.sh" \
  "${ROOT_DIR}/kubectl/09_jobs_and_batch.sh" \
  "${ROOT_DIR}/kubectl/10_llm_observability_stack_checks.sh"; do
  echo
  echo "##### RUNNING: ${script} #####"
  "${script}"
done
