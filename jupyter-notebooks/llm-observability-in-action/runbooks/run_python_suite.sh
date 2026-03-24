#!/usr/bin/env bash
set -euo pipefail

RUNBOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT_DIR="$(cd "${RUNBOOK_DIR}/.." && pwd -P)"

K8S_NAMESPACE="llm-observability"
OPENWEBUI_SERVICE="open-webui"
OLLAMA_SERVICE="ollama"
LANGCHAIN_SERVICE="langchain-demo"
PYTHON_BIN="/usr/local/bin/python3.11"

if [[ -f "${ROOT_DIR}/config.env" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/config.env"
fi

"${PYTHON_BIN}" "${ROOT_DIR}/python/01_namespace_inventory.py" --namespace "${K8S_NAMESPACE:-llm-observability}"
"${PYTHON_BIN}" "${ROOT_DIR}/python/03_workload_health.py" --namespace "${K8S_NAMESPACE:-llm-observability}"
"${PYTHON_BIN}" "${ROOT_DIR}/python/02_service_path_inspector.py" --namespace "${K8S_NAMESPACE:-llm-observability}" --service "${OPENWEBUI_SERVICE:-open-webui}"
"${PYTHON_BIN}" "${ROOT_DIR}/python/02_service_path_inspector.py" --namespace "${K8S_NAMESPACE:-llm-observability}" --service "${OLLAMA_SERVICE:-ollama}"
"${PYTHON_BIN}" "${ROOT_DIR}/python/02_service_path_inspector.py" --namespace "${K8S_NAMESPACE:-llm-observability}" --service "${LANGCHAIN_SERVICE:-langchain-demo}"
"${PYTHON_BIN}" "${ROOT_DIR}/python/04_networking_report.py" --namespace "${K8S_NAMESPACE:-llm-observability}"
