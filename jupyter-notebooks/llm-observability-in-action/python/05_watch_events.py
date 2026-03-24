#!/usr/local/bin/python3.11
"""Watch Kubernetes events in a namespace for troubleshooting."""

from __future__ import annotations

import argparse
import datetime as dt
import sys

from kubernetes import client, config, watch
from kubernetes.client import ApiException


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch namespace events")
    parser.add_argument("--namespace", default="llm-observability", help="Namespace")
    parser.add_argument("--context", default=None, help="Optional kubeconfig context")
    parser.add_argument("--kubeconfig", default=None, help="Optional kubeconfig file")
    parser.add_argument("--in-cluster", action="store_true", help="Use in-cluster auth")
    parser.add_argument("--timeout", type=int, default=300, help="Watch timeout seconds")
    parser.add_argument("--types", default="Normal,Warning", help="Comma-separated event types")
    return parser.parse_args()


def load_cfg(args: argparse.Namespace) -> None:
    if args.in_cluster:
        config.load_incluster_config()
    else:
        config.load_kube_config(config_file=args.kubeconfig, context=args.context)


def main() -> int:
    args = parse_args()
    try:
        load_cfg(args)
    except Exception as exc:
        print(f"Failed to load kube config: {exc}", file=sys.stderr)
        return 1

    allowed = {x.strip() for x in args.types.split(",") if x.strip()}
    core = client.CoreV1Api()
    event_watch = watch.Watch()

    print(f"Watching events in namespace={args.namespace} timeout={args.timeout}s types={sorted(allowed)}")
    print("Press Ctrl+C to stop.")

    try:
        for event in event_watch.stream(
            core.list_namespaced_event,
            namespace=args.namespace,
            timeout_seconds=args.timeout,
        ):
            etype = event.get("type", "UNKNOWN")
            obj: client.CoreV1Event = event["object"]
            event_type = obj.type or "Unknown"
            if allowed and event_type not in allowed:
                continue
            now = dt.datetime.now(dt.timezone.utc).isoformat()
            involved = obj.involved_object
            ref = f"{involved.kind}/{involved.name}" if involved else "<unknown>"
            print(f"[{now}] {etype} eventType={event_type} reason={obj.reason} object={ref} msg={obj.message}")
    except KeyboardInterrupt:
        print("Stopped by user.")
    except ApiException as exc:
        print(f"Watch API error: {exc.status} {exc.reason}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
