from __future__ import annotations

import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _combined_output(proc: subprocess.CompletedProcess[str]) -> str:
    return f"{proc.stdout}\n{proc.stderr}".strip()


def _is_cluster_unreachable(proc: subprocess.CompletedProcess[str]) -> bool:
    output = _combined_output(proc)
    return "Kubernetes cluster unreachable" in output


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary is not available")
def test_helm_template_renders_core_resources() -> None:
    render = _run(
        [
            "helm",
            "template",
            "llm-observability-stack",
            ".",
            "-f",
            "values.local-k3s.example.yaml",
        ]
    )
    assert render.returncode == 0, render.stderr or render.stdout

    manifest = render.stdout
    assert "kind: Deployment" in manifest
    assert "name: langchain-demo" in manifest
    assert "name: ollama" in manifest
    assert "name: open-webui" in manifest
    assert "kind: StatefulSet" in manifest


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary is not available")
def test_helm_install_dry_run_client_succeeds() -> None:
    namespace = "llm-observability-smoke-check"
    install = _run(
        [
            "helm",
            "upgrade",
            "--install",
            "llm-observability-smoke",
            ".",
            "--namespace",
            namespace,
            "--create-namespace",
            "--dry-run=client",
            "--debug",
            "-f",
            "values.local-k3s.example.yaml",
            "--set",
            f"namespace.name={namespace}",
        ]
    )
    if install.returncode != 0 and _is_cluster_unreachable(install):
        pytest.skip("Skipping install dry-run smoke test: Kubernetes cluster is unreachable in this environment.")
    assert install.returncode == 0, _combined_output(install)
    assert "llm-observability-smoke" in install.stdout
    assert namespace in install.stdout


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary is not available")
def test_competition_profile_renders_observability_resources() -> None:
    render = _run(
        [
            "helm",
            "template",
            "llm-observability-stack",
            ".",
            "-f",
            "values.competition-nvidia.example.yaml",
            "--set",
            "langsmith.existingSecret=",
            "--set",
            "openWebUI.existingSecret=",
            "--set",
            "open-webui.webuiSecret.existingSecretName=",
        ]
    )
    assert render.returncode == 0, _combined_output(render)
    manifest = render.stdout
    assert "kind: ServiceMonitor" in manifest
    assert "kind: Probe" in manifest
    assert "kind: PrometheusRule" in manifest
    assert "name: llm-observability-dashboards" in manifest
    assert "llm_observability_time_to_first_token_seconds" in manifest


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary is not available")
def test_geforce_profile_uses_repository_modelfile_and_gpu_worker() -> None:
    render = _run(
        [
            "helm",
            "template",
            "llm-observability-stack",
            ".",
            "-f",
            "values.geforce-940m-k3s.yaml",
        ]
    )
    assert render.returncode == 0, _combined_output(render)
    manifest = render.stdout
    assert "gemma-3-1b-it-Q4_K_M.gguf" in manifest
    assert "node-role.kubernetes.io/worker: \"true\"" in manifest
    assert "nvidia.com/gpu: 1" in manifest
    assert "PARAMETER num_ctx 1024" in manifest

    default_render = _run(["helm", "template", "llm-observability-stack", "."])
    assert default_render.returncode == 0, _combined_output(default_render)
    assert "FROM /models/gguf/gemma-3-1b-it-gguf.gguf" in default_render.stdout


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary is not available")
def test_helm_package_stays_below_secret_limit_budget(tmp_path: Path) -> None:
    package = _run(["helm", "package", ".", "-d", str(tmp_path)])
    assert package.returncode == 0, _combined_output(package)

    archive = next(tmp_path.glob("llm-observability-stack-*.tgz"))
    assert archive.stat().st_size < 900_000

    with tarfile.open(archive, "r:gz") as tgz:
        names = tgz.getnames()

    forbidden_prefixes = [
        "llm-observability-stack/.git/",
        "llm-observability-stack/jupyter-notebooks-2/",
        "llm-observability-stack/docs/",
        "llm-observability-stack/tests/",
    ]
    for prefix in forbidden_prefixes:
        assert not any(name.startswith(prefix) for name in names), prefix

    required_files = [
        "llm-observability-stack/langchain-demo/app.py",
        "llm-observability-stack/Modelfile.gemma-3-1b-it-gguf",
        "llm-observability-stack/dashboards/llm-overview.json",
        "llm-observability-stack/dashboards/nvidia-gpu.json",
        "llm-observability-stack/dashboards/benchmark-results.json",
        "llm-observability-stack/python-toolbox/examples/langsmith_inference_traces.py",
        "llm-observability-stack/python-toolbox/examples/langsmith_dashboard_seed_every_5m.py",
    ]
    for required_file in required_files:
        assert required_file in names, required_file


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary is not available")
def test_secret_wiring_validation_fails_on_mismatched_legacy_and_subchart_values() -> None:
    render = _run(
        [
            "helm",
            "template",
            "llm-observability-stack",
            ".",
            "--set",
            "openWebUI.existingSecret=legacy-secret",
            "--set",
            "open-webui.webuiSecret.existingSecretName=subchart-secret",
        ]
    )
    assert render.returncode != 0
    assert "Secret name mismatch" in (render.stderr + render.stdout)
