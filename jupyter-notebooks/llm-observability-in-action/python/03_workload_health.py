#!/usr/local/bin/python3.11
"""Check rollout/availability health for namespace workloads."""

from __future__ import annotations

import argparse
import sys
from typing import List, Tuple

from kubernetes import client, config
from kubernetes.client import ApiException


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Workload health checks")
    parser.add_argument("--namespace", default="llm-observability", help="Namespace")
    parser.add_argument("--context", default=None, help="Optional kubeconfig context")
    parser.add_argument("--kubeconfig", default=None, help="Optional kubeconfig file")
    parser.add_argument("--in-cluster", action="store_true", help="Use in-cluster auth")
    return parser.parse_args()


def load_cfg(args: argparse.Namespace) -> None:
    if args.in_cluster:
        config.load_incluster_config()
    else:
        config.load_kube_config(config_file=args.kubeconfig, context=args.context)


def print_rows(title: str, rows: List[Tuple[str, str, str]]) -> None:
    print(f"\n=== {title} ===")
    if not rows:
        print("<none>")
        return
    print("kind/name | status | details")
    print("----------+--------+--------")
    for name, status, detail in rows:
        print(f"{name} | {status} | {detail}")


def main() -> int:
    args = parse_args()
    try:
        load_cfg(args)
    except Exception as exc:
        print(f"Failed to load kube config: {exc}", file=sys.stderr)
        return 1

    apps = client.AppsV1Api()
    batch = client.BatchV1Api()

    overall_ok = True
    deployment_rows: List[Tuple[str, str, str]] = []
    stateful_rows: List[Tuple[str, str, str]] = []
    daemon_rows: List[Tuple[str, str, str]] = []
    job_rows: List[Tuple[str, str, str]] = []

    try:
        deployments = apps.list_namespaced_deployment(args.namespace).items
        for d in deployments:
            desired = d.spec.replicas or 0
            available = d.status.available_replicas or 0
            observed = d.status.observed_generation or 0
            generation = d.metadata.generation or 0
            ok = available >= desired and observed >= generation
            status = "OK" if ok else "FAIL"
            if not ok:
                overall_ok = False
            deployment_rows.append(
                (
                    f"deploy/{d.metadata.name}",
                    status,
                    f"desired={desired} available={available} observedGen={observed} gen={generation}",
                )
            )

        statefulsets = apps.list_namespaced_stateful_set(args.namespace).items
        for s in statefulsets:
            desired = s.spec.replicas or 0
            ready = s.status.ready_replicas or 0
            ok = ready >= desired
            status = "OK" if ok else "FAIL"
            if not ok:
                overall_ok = False
            stateful_rows.append((f"sts/{s.metadata.name}", status, f"desired={desired} ready={ready}"))

        daemonsets = apps.list_namespaced_daemon_set(args.namespace).items
        for ds in daemonsets:
            desired = ds.status.desired_number_scheduled or 0
            ready = ds.status.number_ready or 0
            ok = ready >= desired
            status = "OK" if ok else "FAIL"
            if not ok:
                overall_ok = False
            daemon_rows.append((f"ds/{ds.metadata.name}", status, f"desired={desired} ready={ready}"))

        jobs = batch.list_namespaced_job(args.namespace).items
        for j in jobs:
            failed = j.status.failed or 0
            succeeded = j.status.succeeded or 0
            completions = j.spec.completions or 1
            ok = failed == 0 and succeeded >= completions
            status = "OK" if ok else "WARN"
            if failed > 0:
                overall_ok = False
                status = "FAIL"
            job_rows.append((f"job/{j.metadata.name}", status, f"succeeded={succeeded} failed={failed} completions={completions}"))

    except ApiException as exc:
        print(f"API error: {exc.status} {exc.reason}", file=sys.stderr)
        return 2

    print_rows("Deployments", deployment_rows)
    print_rows("StatefulSets", stateful_rows)
    print_rows("DaemonSets", daemon_rows)
    print_rows("Jobs", job_rows)

    if overall_ok:
        print("\nOverall: OK")
        return 0

    print("\nOverall: FAIL")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
