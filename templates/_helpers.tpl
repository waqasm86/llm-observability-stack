{{- define "llm-observability-stack.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "llm-observability-stack.langchainServiceAccountName" -}}
{{- if .Values.langchainDemo.serviceAccount.create -}}
{{- default "langchain-demo" .Values.langchainDemo.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.langchainDemo.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "llm-observability-stack.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s" (include "llm-observability-stack.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "llm-observability-stack.namespace" -}}
{{- default .Release.Namespace .Values.namespace.name -}}
{{- end -}}

{{- define "llm-observability-stack.langsmithSecretName" -}}
{{- if .Values.langsmith.existingSecret -}}
{{- .Values.langsmith.existingSecret -}}
{{- else -}}
langsmith-secrets
{{- end -}}
{{- end -}}

{{- define "llm-observability-stack.webuiSecretName" -}}
{{- $openWebUISubchart := (get .Values "open-webui") | default dict -}}
{{- $webuiSecret := (get $openWebUISubchart "webuiSecret") | default dict -}}
{{- $subchartSecretName := (get $webuiSecret "existingSecretName") | default "" -}}
{{- if $subchartSecretName -}}
{{- $subchartSecretName -}}
{{- else if .Values.openWebUI.existingSecret -}}
{{- .Values.openWebUI.existingSecret -}}
{{- else -}}
open-webui-secrets
{{- end -}}
{{- end -}}

{{- define "llm-observability-stack.webuiSecretKey" -}}
{{- $openWebUISubchart := (get .Values "open-webui") | default dict -}}
{{- $webuiSecret := (get $openWebUISubchart "webuiSecret") | default dict -}}
{{- $subchartSecretKey := (get $webuiSecret "existingSecretKey") | default "" -}}
{{- if $subchartSecretKey -}}
{{- $subchartSecretKey -}}
{{- else if .Values.openWebUI.existingSecretKey -}}
{{- .Values.openWebUI.existingSecretKey -}}
{{- else -}}
WEBUI_SECRET_KEY
{{- end -}}
{{- end -}}

{{- define "llm-observability-stack.manageWebuiSecret" -}}
{{- $openWebUISubchart := (get .Values "open-webui") | default dict -}}
{{- $webuiSecret := (get $openWebUISubchart "webuiSecret") | default dict -}}
{{- $subchartSecretName := (trim ((get $webuiSecret "existingSecretName") | default "")) -}}
{{- $legacySecretName := (trim (.Values.openWebUI.existingSecret | default "")) -}}
{{- if and (eq $subchartSecretName "") (eq $legacySecretName "") -}}
true
{{- end -}}
{{- end -}}

{{- define "llm-observability-stack.etcdFullname" -}}
{{- if .Values.etcd.fullnameOverride -}}
{{- .Values.etcd.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-etcd" (include "llm-observability-stack.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
