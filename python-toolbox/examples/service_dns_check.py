import os
import socket
import time
from urllib.parse import urlparse

import requests


def resolve_port(default: int = 11434) -> int:
    raw = os.getenv("OLLAMA_PORT")
    if not raw:
        return default

    # Kubernetes service env vars may look like: tcp://10.43.54.34:11434
    if raw.startswith("tcp://") or "://" in raw:
        parsed = urlparse(raw)
        if parsed.port:
            return int(parsed.port)

    # Plain integer string case
    try:
        return int(raw)
    except ValueError:
        return default


def resolve_host(default: str = "ollama") -> str:
    raw_host = os.getenv("OLLAMA_SERVICE")
    if raw_host:
        return raw_host

    # If Kubernetes injected OLLAMA_PORT like tcp://10.43.54.34:11434, use hostname from there
    raw_port = os.getenv("OLLAMA_PORT")
    if raw_port and "://" in raw_port:
        parsed = urlparse(raw_port)
        if parsed.hostname:
            return parsed.hostname

    return default


def check_endpoint(name: str, host: str, port: int, path: str):
    url = f"http://{host}:{port}{path}"
    print(f"\n=== {name} ===")
    print("Host:", host)
    print("Port:", port)
    print("URL :", url)

    try:
        resolved_ip = socket.gethostbyname(host)
        print("DNS :", resolved_ip)
    except Exception as e:
        print("DNS resolution failed:", repr(e))
        return

    try:
        start = time.perf_counter()
        response = requests.get(url, timeout=10)
        elapsed = time.perf_counter() - start
        print("HTTP status:", response.status_code)
        print("Elapsed    :", f"{elapsed:.3f}s")
        body = response.text[:500].strip()
        print("Body       :", body if body else "<empty>")
    except Exception as e:
        print("HTTP request failed:", repr(e))


if __name__ == "__main__":
    ollama_host = resolve_host("ollama")
    ollama_port = resolve_port(11434)

    targets = [
        ("Ollama tags", ollama_host, ollama_port, "/api/tags"),
        ("Langchain demo health", "langchain-demo", 8000, "/healthz"),
        ("Open WebUI root", "open-webui", 8080, "/"),
        ("Redis ping via TCP check target", "open-webui-redis", 6379, "/"),
    ]

    for name, host, port, path in targets:
        # HTTP only for HTTP services
        if port == 6379:
            print(f"\n=== {name} ===")
            print("Host:", host)
            print("Port:", port)
            try:
                resolved_ip = socket.gethostbyname(host)
                print("DNS :", resolved_ip)
                sock = socket.create_connection((host, port), timeout=5)
                print("TCP :", "connected")
                sock.close()
            except Exception as e:
                print("TCP check failed:", repr(e))
            continue

        check_endpoint(name, host, port, path)
