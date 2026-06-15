#!/usr/bin/env python3
"""Run repeatable Ollama streaming benchmarks and optionally publish summary metrics."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * quantile)))
    return ordered[index]


def run_once(url: str, model: str, prompt: str, timeout: float) -> dict[str, Any]:
    payload = json.dumps(
        {"model": model, "prompt": prompt, "stream": True, "options": {"temperature": 0}}
    ).encode()
    request = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    started = time.perf_counter()
    first_token_at: float | None = None
    final: dict[str, Any] = {}
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw_line in response:
            if not raw_line.strip():
                continue
            chunk = json.loads(raw_line)
            if first_token_at is None and chunk.get("response"):
                first_token_at = time.perf_counter()
            if chunk.get("done") is True:
                final = chunk
    finished = time.perf_counter()
    generated_tokens = int(final.get("eval_count", 0))
    eval_duration = float(final.get("eval_duration", 0)) / 1_000_000_000
    return {
        "success": True,
        "duration_seconds": finished - started,
        "ttft_seconds": (first_token_at or finished) - started,
        "prompt_tokens": int(final.get("prompt_eval_count", 0)),
        "generated_tokens": generated_tokens,
        "tokens_per_second": generated_tokens / eval_duration if eval_duration > 0 else 0.0,
    }


def push_metrics(pushgateway: str, job: str, model: str, summary: dict[str, Any]) -> None:
    labels = f'model="{model}"'
    lines = [
        "# TYPE llm_benchmark_success gauge",
        f"llm_benchmark_success{{{labels}}} 1",
        "# TYPE llm_benchmark_ttft_seconds gauge",
        f"llm_benchmark_ttft_seconds{{{labels},quantile=\"0.50\"}} {summary['ttft_p50_seconds']}",
        f"llm_benchmark_ttft_seconds{{{labels},quantile=\"0.95\"}} {summary['ttft_p95_seconds']}",
        "# TYPE llm_benchmark_tokens_per_second gauge",
        f"llm_benchmark_tokens_per_second{{{labels}}} {summary['tokens_per_second_mean']}",
        "# TYPE llm_benchmark_duration_seconds gauge",
        f"llm_benchmark_duration_seconds{{{labels},quantile=\"0.95\"}} {summary['duration_p95_seconds']}",
        "",
    ]
    endpoint = f"{pushgateway.rstrip('/')}/metrics/job/{job}"
    request = urllib.request.Request(
        endpoint,
        data="\n".join(lines).encode(),
        headers={"Content-Type": "text/plain; version=0.0.4"},
        method="PUT",
    )
    with urllib.request.urlopen(request, timeout=15):
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:11434/api/generate")
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt", default="Explain GPU observability in three concise sentences.")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--warmup-runs", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--pushgateway", default="")
    parser.add_argument("--push-job", default="llm_competition_benchmark")
    parser.add_argument("--output", type=Path, default=Path("artifacts/benchmark.json"))
    args = parser.parse_args()

    for _ in range(args.warmup_runs):
        run_once(args.url, args.model, args.prompt, args.timeout)
    results = [run_once(args.url, args.model, args.prompt, args.timeout) for _ in range(args.runs)]
    ttft = [float(item["ttft_seconds"]) for item in results]
    durations = [float(item["duration_seconds"]) for item in results]
    throughput = [float(item["tokens_per_second"]) for item in results]
    summary = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "url": args.url,
        "runs": args.runs,
        "warmup_runs": args.warmup_runs,
        "ttft_p50_seconds": percentile(ttft, 0.50),
        "ttft_p95_seconds": percentile(ttft, 0.95),
        "duration_p50_seconds": percentile(durations, 0.50),
        "duration_p95_seconds": percentile(durations, 0.95),
        "tokens_per_second_mean": statistics.fmean(throughput),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if args.pushgateway:
        push_metrics(args.pushgateway, args.push_job, args.model, summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        raise SystemExit(f"benchmark request failed: {exc}") from exc
