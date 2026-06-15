# GitHub Publishing Guide

Repository target:

- https://github.com/waqasm86/llm-observability-stack

## Daily publish workflow

Run from `llm-observability-stack/`:

```bash
git checkout main
git pull --rebase origin main
```

Review changes and ensure no secrets are staged:

```bash
git status --short
git diff -- values.yaml values.local-k3s.example.yaml README.md .gitignore
```

Validate chart rendering:

```bash
helm lint .
helm template llm-observability-stack . >/tmp/rendered-default.yaml
helm template llm-observability-stack . -f values.local-k3s.example.yaml >/tmp/rendered-local.yaml
```

Stage, commit, and push:

```bash
git add .
git commit -m "rebrand: position stack as EdgeLLM Observability for NVIDIA edge AI"
git push origin main
```

## EdgeLLM Pre-Push Checklist

- no GGUF model binaries
- no secrets, kubeconfigs, private values, or credentials
- `helm lint .` passes
- application and Helm tests pass
- README says pilot-ready and does not claim production proof
- competition documents are present
- verified local results and sanitized benchmark evidence are present
- no false Lenovo or NVIDIA sponsorship, endorsement, or certification claims

Recommended local checks:

```bash
git status --short
git diff --cached --stat
git diff --cached | rg -n 'BEGIN .*PRIVATE KEY|sk-[A-Za-z0-9]{20,}|kubeconfig'
find . -type f \( -name '*.gguf' -o -name '*.safetensors' \) -not -path './.git/*'
```

## Remote setup (first time only)

```bash
git remote add origin https://github.com/waqasm86/llm-observability-stack.git
# or, if origin already exists
git remote set-url origin https://github.com/waqasm86/llm-observability-stack.git
```

## Secret guard

Do not commit:

- `values.local-k3s.yaml`
- `.webui_secret_key`
- `.env*`
- `*.pem`, `*.key`, `*.crt`
- `*.kubeconfig`
- rendered local artifacts and private debug dumps
- local screenshots in `pictures/`
- private customer evidence under `artifacts/private/`

These are blocked by `.gitignore` and `.helmignore`.

## Current repository hygiene notes

Before `git add .`, make sure these remain ignored or intentionally excluded:

- `values.local-k3s.yaml`
- notebook checkpoint directories
- generated notebook artifacts
- duplicated local working directories such as `jupyter-notebooks-2/`
- rendered manifests and private debug dumps

## Size guard

Check repository size before pushing large changes:

```bash
du -sh .
find . -type f -printf '%s %p\n' | sort -nr | head -30
```
