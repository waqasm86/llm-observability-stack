#!/usr/local/bin/python3.11
"""Trace service routing path: selector -> pods -> endpoints -> routes."""

from __future__ import annotations

import argparse
import sys
from typing import Dict, List

from kubernetes import client, config
from kubernetes.client import ApiException


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect end-to-end service path")
    parser.add_argument("--namespace", default="llm-observability", help="Namespace")
    parser.add_argument("--service", required=True, help="Service name")
    parser.add_argument("--context", default=None, help="Optional kubeconfig context")
    parser.add_argument("--kubeconfig", default=None, help="Optional kubeconfig file")
    parser.add_argument("--in-cluster", action="store_true", help="Use in-cluster auth")
    return parser.parse_args()


def load_cfg(args: argparse.Namespace) -> None:
    if args.in_cluster:
        config.load_incluster_config()
    else:
        config.load_kube_config(config_file=args.kubeconfig, context=args.context)


def selector_to_query(selector: Dict[str, str]) -> str:
    if not selector:
        return ""
    return ",".join(f"{k}={v}" for k, v in selector.items())


def print_header(label: str) -> None:
    print(f"\n=== {label} ===")


def ingress_refs_service(ing: client.V1Ingress, service_name: str) -> bool:
    if not ing.spec:
        return False
    for rule in ing.spec.rules or []:
        if not rule.http:
            continue
        for path in rule.http.paths or []:
            backend_svc = path.backend.service if path.backend else None
            if backend_svc and backend_svc.name == service_name:
                return True
    return False


def http_route_refs_service(route: dict, namespace: str, service_name: str) -> bool:
    spec = route.get("spec", {})
    for rule in spec.get("rules", []):
        for backend_ref in rule.get("backendRefs", []):
            if backend_ref.get("name") != service_name:
                continue
            backend_ns = backend_ref.get("namespace", namespace)
            if backend_ns == namespace:
                return True
    return False


def main() -> int:
    args = parse_args()
    try:
        load_cfg(args)
    except Exception as exc:
        print(f"Failed to load kube config: {exc}", file=sys.stderr)
        return 1

    core = client.CoreV1Api()
    net = client.NetworkingV1Api()
    discovery = client.DiscoveryV1Api()
    custom = client.CustomObjectsApi()

    try:
        svc = core.read_namespaced_service(name=args.service, namespace=args.namespace)
    except ApiException as exc:
        if exc.status == 404:
            print(f"Service not found: {args.namespace}/{args.service}", file=sys.stderr)
            return 2
        print(f"API error: {exc.status} {exc.reason}", file=sys.stderr)
        return 2

    selector = svc.spec.selector or {}
    selector_query = selector_to_query(selector)

    print_header("Service")
    print(f"name: {svc.metadata.name}")
    print(f"namespace: {svc.metadata.namespace}")
    print(f"type: {svc.spec.type}")
    print(f"cluster_ip: {svc.spec.cluster_ip}")
    print(f"selector: {selector if selector else '<none>'}")
    print(
        "ports: "
        f"{[{'name': p.name, 'port': p.port, 'targetPort': p.target_port, 'protocol': p.protocol} for p in (svc.spec.ports or [])]}"
    )

    print_header("Selected Pods")
    pods = []
    if selector_query:
        pods = core.list_namespaced_pod(namespace=args.namespace, label_selector=selector_query).items
    if not pods:
        print("No pods matched service selector or selector is empty.")
    for pod in pods:
        ready = all(cs.ready for cs in (pod.status.container_statuses or [])) if pod.status.container_statuses else False
        print(
            f"- {pod.metadata.name} phase={pod.status.phase} ready={ready} "
            f"pod_ip={pod.status.pod_ip} node={pod.spec.node_name}"
        )

    print_header("Endpoints")
    try:
        ep = core.read_namespaced_endpoints(name=args.service, namespace=args.namespace)
        if not ep.subsets:
            print("No endpoint subsets.")
        else:
            for subset in ep.subsets:
                addrs = [a.ip for a in (subset.addresses or [])]
                not_ready = [a.ip for a in (subset.not_ready_addresses or [])]
                ports = [f"{p.name or ''}:{p.port}/{p.protocol}" for p in (subset.ports or [])]
                print(f"addresses={addrs or []} not_ready={not_ready or []} ports={ports or []}")
    except ApiException as exc:
        print(f"Failed to read Endpoints: {exc.status} {exc.reason}")

    print_header("EndpointSlices")
    try:
        slices = discovery.list_namespaced_endpoint_slice(
            namespace=args.namespace,
            label_selector=f"kubernetes.io/service-name={args.service}",
        ).items
        if not slices:
            print("No EndpointSlices found.")
        for eps in slices:
            addresses: List[str] = []
            for endpoint in eps.endpoints or []:
                addresses.extend(endpoint.addresses or [])
            ports = [f"{p.name or ''}:{p.port}/{p.protocol}" for p in (eps.ports or [])]
            print(f"- {eps.metadata.name} addresses={addresses or []} ports={ports or []}")
    except ApiException as exc:
        print(f"Failed to list EndpointSlices: {exc.status} {exc.reason}")

    print_header("Ingress / HTTPRoute references")
    try:
        ingresses = net.list_namespaced_ingress(namespace=args.namespace).items
    except ApiException as exc:
        print(f"Failed to list Ingress: {exc.status} {exc.reason}")
        ingresses = []
    ingress_hits = [ing.metadata.name for ing in ingresses if ingress_refs_service(ing, args.service)]
    print(f"Ingress refs: {ingress_hits or []}")

    route_hits: List[str] = []
    try:
        routes = custom.list_namespaced_custom_object(
            group="gateway.networking.k8s.io",
            version="v1",
            namespace=args.namespace,
            plural="httproutes",
        )
        for route in routes.get("items", []):
            if http_route_refs_service(route, args.namespace, args.service):
                route_hits.append(route.get("metadata", {}).get("name", "<unknown>"))
    except ApiException as exc:
        if exc.status != 404:
            print(f"Failed to list HTTPRoutes: {exc.status} {exc.reason}")
    print(f"HTTPRoute refs: {route_hits or []}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
