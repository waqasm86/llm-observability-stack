import os
from langsmith import Client

api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
project = os.getenv("LANGSMITH_PROJECT", "default")

if not api_key:
    raise SystemExit("LANGSMITH_API_KEY or LANGCHAIN_API_KEY is not set")

client = Client(api_url=endpoint, api_key=api_key)
print(f"endpoint: {endpoint}")
print(f"project: {project}")
projects = list(client.list_projects(limit=5))
print(f"retrieved {len(projects)} project(s)")
for item in projects:
    print(f"- {item.name}")
