#!/usr/bin/env bash
set -euo pipefail

LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT_DIR="$(cd "${LIB_DIR}/.." && pwd -P)"

if [[ -f "${ROOT_DIR}/config.env" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/config.env"
fi

: "${K8S_NAMESPACE:=llm-observability}"
: "${K8S_CONTEXT:=}"
: "${K8S_RELEASE:=llm-observability-stack}"
: "${OPENWEBUI_SERVICE:=open-webui}"
: "${OLLAMA_SERVICE:=ollama}"
: "${LANGCHAIN_SERVICE:=langchain-demo}"
: "${PYTHON_TOOLBOX_DEPLOYMENT:=python-toolbox}"
: "${APPLY_CHANGES:=0}"

KCTL_BIN=(kubectl)
if [[ -n "${K8S_CONTEXT}" ]]; then
  KCTL_BIN+=(--context "${K8S_CONTEXT}")
fi

log_section() {
  printf '\n==== %s ====\n' "$1"
}

log_info() {
  printf '[INFO] %s\n' "$1"
}

log_warn() {
  printf '[WARN] %s\n' "$1" >&2
}

require_cmds() {
  local cmd
  for cmd in "$@"; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
      printf '[ERROR] Missing required command: %s\n' "${cmd}" >&2
      exit 1
    fi
  done
}

print_runtime_context() {
  log_info "Namespace: ${K8S_NAMESPACE}"
  if [[ -n "${K8S_CONTEXT}" ]]; then
    log_info "Context: ${K8S_CONTEXT}"
  else
    log_info "Context: kubectl current-context"
  fi
  log_info "Release: ${K8S_RELEASE}"
  log_info "APPLY_CHANGES: ${APPLY_CHANGES}"
}

run_cmd() {
  printf '+ %s\n' "$*"
  "$@"
}

is_mutating_kubectl() {
  local verb="${1:-}"
  local subverb="${2:-}"

  case "${verb}" in
    apply|create|delete|replace|patch|edit|scale|set|label|annotate|autoscale|run|expose|taint|cordon|uncordon|drain)
      return 0
      ;;
    rollout)
      case "${subverb}" in
        restart|undo|pause|resume)
          return 0
          ;;
      esac
      ;;
  esac

  return 1
}

kctl() {
  local verb="${1:-}"
  local subverb="${2:-}"
  if is_mutating_kubectl "${verb}" "${subverb}" && [[ "${APPLY_CHANGES}" != "1" ]]; then
    log_warn "Skipping mutating command in read-only mode: kubectl $*"
    return 0
  fi
  run_cmd "${KCTL_BIN[@]}" "$@"
}

kctl_ns() {
  local verb="${1:-}"
  local subverb="${2:-}"
  if is_mutating_kubectl "${verb}" "${subverb}" && [[ "${APPLY_CHANGES}" != "1" ]]; then
    log_warn "Skipping mutating command in read-only mode: kubectl -n ${K8S_NAMESPACE} $*"
    return 0
  fi
  run_cmd "${KCTL_BIN[@]}" -n "${K8S_NAMESPACE}" "$@"
}

kctl_try() {
  if ! kctl "$@"; then
    log_warn "Command failed (continuing): kubectl $*"
  fi
}

kctl_ns_try() {
  if ! kctl_ns "$@"; then
    log_warn "Command failed (continuing): kubectl -n ${K8S_NAMESPACE} $*"
  fi
}

kctl_capture() {
  "${KCTL_BIN[@]}" "$@"
}

kctl_ns_capture() {
  "${KCTL_BIN[@]}" -n "${K8S_NAMESPACE}" "$@"
}

resource_exists_ns() {
  kctl_ns_capture get "$1" >/dev/null 2>&1
}
