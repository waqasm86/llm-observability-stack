import os
import time
import requests

base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
model = os.getenv("OLLAMA_MODEL", "gemma3-1b-it-gguf-local")

resp = requests.get(f"{base_url}/api/tags", timeout=10)
resp.raise_for_status()
print("models:")
print(resp.text)

payload = {
    "model": model,
    "messages": [{"role": "user", "content": "Reply with one short sentence saying the stack is healthy."}],
    "stream": False,
}
start = time.perf_counter()
resp = requests.post(f"{base_url}/api/chat", json=payload, timeout=60)
resp.raise_for_status()
elapsed = time.perf_counter() - start
print(f"chat completed in {elapsed:.2f}s")
print(resp.json())
