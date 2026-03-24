#!/usr/local/bin/python3.11
"""Build a namespace networking report and optional JSON output."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List

from kubernetes import client, config
from kubernetes.client import ApiException


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Networking report")
    parser.add_argument("--namespace", default="llm-observability", help="Namespace")
    parser.add_argument("--context", default=None, help="Optional kubeconfig context")
    parser.add_argument("--kubeconfig", default=None, help="Optional kubeconfig file")
    parser.add_argument("--in-cluster", action="store_true", help="Use in-cluster auth")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    return parser.parse_args()


def load_cfg(args: argparse.Namespace) -> None:
    if args.in_cluster:
        config.load_incluster_config()
    else:
        config.load_kube_config(config_file=args.kubeconfig, context=args.context)


def match_selector(labels: Dict[str, str] | None, selector: Dict[str, str] | None) -> bool:
    if not selector:
        return False
    labels = labels or {}
    return all(labels.get(k) == v for k, v in selector.items())


def main() -> int:
    args = parse_args()
    try:
        load_cfg(args)
    except Exception as exc:
        print(f"Failed to load kube config: {exc}", file=sys.stderr)
        return 1

    core = client.CoreV1Api()
    discovery = client.DiscoveryV1Api()
    net = client.NetworkingV1Api()

    try:
        pods = core.list_namespaced_pod(args.namespace).items
        svcs = core.list_namespaced_service(args.namespace).items
        endpoints = core.list_namespaced_endpoints(args.namespace).items
        endpoint_slices = discovery.list_namespaced_endpoint_slice(args.namespace).items
        ingresses = net.list_namespaced_ingress(args.namespace).items
    except ApiException as exc:
        print(f"API error: {exc.status} {exc.reason}", file=sys.stderr)
        return 2

    pod_index = {
        p.metadata.name: {
            "name": p.metadata.name,
            "labels": p.metadata.labels or {},
            "pod_ip": p.status.pod_ip,
            "node": p.spec.node_name,
            "phase": p.status.phase,
        }
        for p in pods
    }

    endpoints_by_name: Dict[str, List[str]] = {}
    for ep in endpoints:
        addrs: List[str] = []
        for subset in ep.subsets or []:
            addrs.extend([a.ip for a in (subset.addresses or [])])
        endpoints_by_name[ep.metadata.name] = addrs

    epslice_by_service: Dict[str, List[str]] = {}
    for eps in endpoint_slices:
        svc_name = (eps.metadata.labels or {}).get("kubernetes.io/service-name")
        if not svc_name:
            continue
        epslice_by_service.setdefault(svc_name, [])
        for endpoint in eps.endpoints or []:
            epslice_by_service[svc_name].extend(endpoint.addresses or [])

    ingress_map: Dict[str, List[str]] = {}
    for ing in ingresses:
        for rule in ing.spec.rules or []:
            if not rule.http:
                continue
            for path in rule.http.paths or []:
                backend = path.backend.service if path.backend else None
                if not backend:
                    continue
                ingress_map.setdefault(backend.name, [])
                ingress_map[backend.name].append(ing.metadata.name)

    report: Dict[str, object] = {
        "namespace": args.namespace,
        "services": [],
    }

    for svc in svcs:
        selector = svc.spec.selector or {}
        selected_pods = [pod["name"] for pod in pod_index.values() if match_selector(pod["labels"], selector)]
        ports = [{"name": p.name, "port": p.port, "targetPort": p.target_port, "protocol": p.protocol} for p in (svc.spec.ports or [])]
        svc_record = {
            "service": svc.metadata.name,
            "type": svc.spec.type,
            "cluster_ip": svc.spec.cluster_ip,
            "dns": f"{svc.metadata.name}.{args.namespace}.svc.cluster.local",
            "selector": selector,
            "ports": ports,
            "selected_pods": selected_pods,
            "endpoints": endpoints_by_name.get(svc.metadata.name, []),
            "endpoint_slices": epslice_by_service.get(svc.metadata.name, []),
            "ingress_refs": ingress_map.get(svc.metadata.name, []),
        }
        report["services"].append(svc_record)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print(f"Namespace: {args.namespace}")
    for svc in report["services"]:  # type: ignore[index]
        print("\n---")
        print(f"service: {svc['service']}")
        print(f"type: {svc['type']} cluster_ip: {svc['cluster_ip']}")
        print(f"dns: {svc['dns']}")
        print(f"selector: {svc['selector'] or '<none>'}")
        print(f"ports: {svc['ports']}")
        print(f"selected_pods: {svc['selected_pods']}")
        print(f"endpoints: {svc['endpoints']}")
        print(f"endpoint_slices: {svc['endpoint_slices']}")
        print(f"ingress_refs: {svc['ingress_refs']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
