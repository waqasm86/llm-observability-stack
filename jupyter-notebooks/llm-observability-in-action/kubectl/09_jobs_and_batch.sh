#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmds kubectl
print_runtime_context

log_section "Batch resources"
kctl_ns_try get job,cronjob -o wide

log_section "Jobs detail"
while IFS= read -r job_name; do
  [[ -z "${job_name}" ]] && continue
  kctl_ns_try describe "job/${job_name}"
done < <(kctl_ns_capture get job -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)

log_section "CronJobs detail"
while IFS= read -r cj_name; do
  [[ -z "${cj_name}" ]] && continue
  kctl_ns_try describe "cronjob/${cj_name}"
done < <(kctl_ns_capture get cronjob -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)

if [[ "${APPLY_CHANGES}" == "1" ]]; then
  log_section "Mutating demo: run smoke job"
  kctl_ns apply -f "${SCRIPT_DIR}/../manifests/workloads/job.kubectl-smoke.yaml"
  kctl_ns wait --for=condition=Complete job/kubectl-smoke --timeout=180s
  kctl_ns logs job/kubectl-smoke
else
  log_info "Read-only mode: skipping job creation. Set APPLY_CHANGES=1 to run smoke job manifest."
fi
