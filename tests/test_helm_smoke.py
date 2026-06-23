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
    assert 'url: "prometheus-blackbox-exporter.monitoring.svc.cluster.local:9115"' in manifest
    assert "url: http://prometheus-blackbox-exporter" not in manifest
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
    assert 'helm.sh/resource-policy: keep' in manifest
    assert "readOnly: true" in manifest
    assert "/bin/ollama rm" not in manifest

    default_render = _run(["helm", "template", "llm-observability-stack", "."])
    assert default_render.returncode == 0, _combined_output(default_render)
    assert "FROM /models/gguf/gemma-3-1b-it-gguf.gguf" in default_render.stdout
    assert "/bin/ollama rm" not in default_render.stdout


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary is not available")
def test_cpu_profile_disables_nvidia_scheduling() -> None:
    render = _run(
        [
            "helm",
            "template",
            "llm-observability-stack",
            ".",
            "-f",
            "values.cpu-k3s.yaml",
        ]
    )
    assert render.returncode == 0, _combined_output(render)
    manifest = render.stdout
    assert "name: ollama" in manifest
    assert "runtimeClassName: \"nvidia\"" not in manifest
    assert "runtimeClassName: nvidia" not in manifest
    assert "nvidia.com/gpu: 1" not in manifest
    assert "nvidia.com/gpu.present" not in manifest
    assert "name: dcgm-exporter" not in manifest
    assert "readOnly: true" in manifest
    assert "/bin/ollama rm" not in manifest


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary is not available")
def test_generated_cpu_overlay_can_override_enterprise_gpu_profile() -> None:
    render = _run(
        [
            "helm",
            "template",
            "llm-observability-stack",
            ".",
            "-f",
            "values.enterprise-pilot-k3s.yaml",
            "--set",
            "runtime.accelerator=cpu",
            "--set",
            "nvidia.runtimeClassName=",
            "--set",
            "nvidia.gpuCount=0",
            "--set",
            "dcgm-exporter.enabled=false",
            "--set",
            "monitoring.dcgmExporter.serviceMonitor.enabled=false",
            "--set",
            "ollama.runtimeClassName=",
            "--set",
            "ollama.nodeSelector=null",
            "--set",
            "ollama.ollama.gpu.enabled=false",
            "--set",
            "ollama.ollama.gpu.number=0",
        ]
    )
    assert render.returncode == 0, _combined_output(render)
    manifest = render.stdout
    assert "runtimeClassName: \"nvidia\"" not in manifest
    assert "runtimeClassName: nvidia" not in manifest
    assert "nvidia.com/gpu: 1" not in manifest
    assert "nvidia.com/gpu.present" not in manifest


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary is not available")
def test_generated_nvidia_overlay_uses_gpu_resource_without_static_node_label() -> None:
    render = _run(
        [
            "helm",
            "template",
            "llm-observability-stack",
            ".",
            "-f",
            "values.enterprise-pilot-k3s.yaml",
            "--set",
            "runtime.accelerator=nvidia",
            "--set",
            "nvidia.runtimeClassName=nvidia",
            "--set",
            "nvidia.gpuCount=1",
            "--set",
            "ollama.runtimeClassName=nvidia",
            "--set",
            "ollama.nodeSelector=null",
            "--set",
            "ollama.ollama.gpu.enabled=true",
            "--set",
            "ollama.ollama.gpu.number=1",
        ]
    )
    assert render.returncode == 0, _combined_output(render)
    manifest = render.stdout
    assert "runtimeClassName: \"nvidia\"" in manifest
    assert "nvidia.com/gpu: 1" in manifest
    assert "nvidia.com/gpu.present" not in manifest


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary is not available")
def test_model_cleanup_is_rejected() -> None:
    render = _run(
        [
            "helm",
            "template",
            "llm-observability-stack",
            ".",
            "--set",
            "ollama.ollama.models.clean=true",
        ]
    )
    assert render.returncode != 0
    assert "models.clean must stay false" in _combined_output(render)


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary is not available")
def test_helm_package_stays_below_secret_limit_budget(tmp_path: Path) -> None:
    package = _run(["helm", "package", ".", "-d", str(tmp_path)])
    assert package.returncode == 0, _combined_output(package)

    archive = next(tmp_path.glob("llm-observability-stack-*.tgz"))
    assert archive.stat().st_size < 3_000_000

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
        "llm-observability-stack/charts/gpu-operator/Chart.yaml",
        "llm-observability-stack/charts/nvidia-device-plugin/Chart.yaml",
        "llm-observability-stack/charts/dcgm-exporter/Chart.yaml",
        "llm-observability-stack/charts/kube-prometheus-stack/Chart.yaml",
        "llm-observability-stack/charts/opentelemetry-collector/Chart.yaml",
        "llm-observability-stack/charts/opentelemetry-operator/Chart.yaml",
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
