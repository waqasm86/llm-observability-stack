#!/usr/local/bin/python3.11
"""Comprehensive namespace inventory for llm-observability in-action."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from typing import Iterable, List

from kubernetes import client, config
from kubernetes.client import ApiException


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Namespace inventory")
    parser.add_argument("--namespace", default="llm-observability", help="Namespace to inspect")
    parser.add_argument("--context", default=None, help="Kubeconfig context")
    parser.add_argument("--kubeconfig", default=None, help="Kubeconfig path")
    parser.add_argument("--in-cluster", action="store_true", help="Use in-cluster config")
    return parser.parse_args()


def load_cfg(args: argparse.Namespace) -> None:
    if args.in_cluster:
        config.load_incluster_config()
    else:
        config.load_kube_config(config_file=args.kubeconfig, context=args.context)


def table(title: str, headers: List[str], rows: List[List[str]]) -> None:
    print(f"\n=== {title} ===")
    if not rows:
        print("<none>")
        return
    widths = [len(h) for h in headers]
    for row in rows:
        for i, v in enumerate(row):
            widths[i] = max(widths[i], len(str(v)))

    def fmt(r: Iterable[str]) -> str:
        return " | ".join(str(v).ljust(widths[i]) for i, v in enumerate(r))

    print(fmt(headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(fmt(row))


def fmt_selector(selector: dict | None) -> str:
    if not selector:
        return "-"
    return ",".join(f"{k}={v}" for k, v in sorted(selector.items()))


def fmt_ports(ports: Iterable[object] | None) -> str:
    if not ports:
        return "-"
    out: List[str] = []
    for p in ports:
        name = getattr(p, "name", "") or ""
        port = getattr(p, "port", "")
        target = getattr(p, "target_port", None)
        proto = getattr(p, "protocol", "TCP")
        left = f"{name}:{port}" if name else str(port)
        if target is None:
            out.append(f"{left}/{proto}")
        else:
            out.append(f"{left}->{target}/{proto}")
    return ", ".join(out)


def summarize(namespace: str) -> int:
    core = client.CoreV1Api()
    apps = client.AppsV1Api()
    batch = client.BatchV1Api()
    net = client.NetworkingV1Api()
    discovery = client.DiscoveryV1Api()

    try:
        pods = core.list_namespaced_pod(namespace).items
        services = core.list_namespaced_service(namespace).items
        endpoints = core.list_namespaced_endpoints(namespace).items
        endpoint_slices = discovery.list_namespaced_endpoint_slice(namespace).items
        configmaps = core.list_namespaced_config_map(namespace).items
        secrets = core.list_namespaced_secret(namespace).items
        pvcs = core.list_namespaced_persistent_volume_claim(namespace).items
        deployments = apps.list_namespaced_deployment(namespace).items
        statefulsets = apps.list_namespaced_stateful_set(namespace).items
        daemonsets = apps.list_namespaced_daemon_set(namespace).items
        jobs = batch.list_namespaced_job(namespace).items
        cronjobs = batch.list_namespaced_cron_job(namespace).items
        ingresses = net.list_namespaced_ingress(namespace).items
        netpols = net.list_namespaced_network_policy(namespace).items
    except ApiException as exc:
        print(f"API error: {exc.status} {exc.reason}", file=sys.stderr)
        print(exc.body or "", file=sys.stderr)
        return 2

    pod_rows: List[List[str]] = []
    for p in pods:
        ready = sum(1 for cs in (p.status.container_statuses or []) if cs.ready)
        total = len(p.status.container_statuses or [])
        restarts = sum((cs.restart_count or 0) for cs in (p.status.container_statuses or []))
        pod_rows.append(
            [
                p.metadata.name,
                p.status.phase or "",
                f"{ready}/{total}",
                str(restarts),
                p.status.pod_ip or "",
                p.spec.node_name or "",
            ]
        )

    svc_rows: List[List[str]] = []
    for s in services:
        svc_rows.append(
            [
                s.metadata.name,
                s.spec.type or "",
                s.spec.cluster_ip or "",
                fmt_ports(s.spec.ports),
                fmt_selector(s.spec.selector),
            ]
        )

    ep_rows: List[List[str]] = []
    for ep in endpoints:
        addresses: List[str] = []
        ports: List[str] = []
        for subset in ep.subsets or []:
            addresses.extend([a.ip for a in (subset.addresses or [])])
            ports.extend([f"{p.name or ''}:{p.port}/{p.protocol}" for p in (subset.ports or [])])
        ep_rows.append([ep.metadata.name, ",".join(addresses) if addresses else "-", ",".join(ports) if ports else "-"])

    eps_rows: List[List[str]] = []
    for eps in endpoint_slices:
        svc_name = (eps.metadata.labels or {}).get("kubernetes.io/service-name", "-")
        addresses: List[str] = []
        for e in eps.endpoints or []:
            addresses.extend(e.addresses or [])
        ports = [f"{p.name or ''}:{p.port}/{p.protocol}" for p in (eps.ports or [])]
        eps_rows.append([eps.metadata.name, svc_name, ",".join(addresses) if addresses else "-", ",".join(ports) if ports else "-"])

    wl_rows: List[List[str]] = []
    for d in deployments:
        wl_rows.append(["Deployment", d.metadata.name, str(d.spec.replicas or 0), str(d.status.available_replicas or 0)])
    for s in statefulsets:
        wl_rows.append(["StatefulSet", s.metadata.name, str(s.spec.replicas or 0), str(s.status.ready_replicas or 0)])
    for ds in daemonsets:
        wl_rows.append(["DaemonSet", ds.metadata.name, str(ds.status.desired_number_scheduled or 0), str(ds.status.number_ready or 0)])
    for j in jobs:
        wl_rows.append(["Job", j.metadata.name, str(j.spec.completions or 1), str(j.status.succeeded or 0)])
    for cj in cronjobs:
        wl_rows.append(["CronJob", cj.metadata.name, cj.spec.schedule or "", cj.spec.concurrency_policy or ""])

    cfg_rows: List[List[str]] = []
    cfg_rows.append(["ConfigMaps", str(len(configmaps))])
    cfg_rows.append(["Secrets", str(len(secrets))])
    cfg_rows.append(["PVCs", str(len(pvcs))])
    cfg_rows.append(["Ingresses", str(len(ingresses))])
    cfg_rows.append(["NetworkPolicies", str(len(netpols))])

    print(f"Timestamp: {dt.datetime.now(dt.timezone.utc).isoformat()}")
    print(f"Namespace: {namespace}")

    table("Pods", ["name", "phase", "ready", "restarts", "pod_ip", "node"], pod_rows)
    table("Services", ["name", "type", "cluster_ip", "ports", "selector"], svc_rows)
    table("Endpoints", ["name", "addresses", "ports"], ep_rows)
    table("EndpointSlices", ["name", "service", "addresses", "ports"], eps_rows)
    table("Workloads", ["kind", "name", "desired", "current/ready"], wl_rows)
    table("Config/Storage summary", ["resource", "count"], cfg_rows)

    return 0


def main() -> int:
    args = parse_args()
    try:
        load_cfg(args)
    except Exception as exc:  # pragma: no cover
        print(f"Failed to load kube config: {exc}", file=sys.stderr)
        return 1
    return summarize(args.namespace)


if __name__ == "__main__":
    raise SystemExit(main())
