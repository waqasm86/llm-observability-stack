import os
import redis

host = os.getenv("REDIS_HOST", "open-webui-redis")
port = int(os.getenv("REDIS_PORT", "6379"))
client = redis.Redis(host=host, port=port, socket_connect_timeout=3, socket_timeout=3)
print("PING:", client.ping())
