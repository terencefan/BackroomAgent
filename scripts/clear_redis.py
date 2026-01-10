import os
import sys

import redis

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backroom_agent.constants import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT


def clear_cache():
    print(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}...")
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        r.ping()

        # Pattern to match - Specific to Init Node Intro
        patterns = [
            "backroom:init_node_intro:*",
            "backroom:init_node_json_v1:*",
            # Add other patterns here if needed in future
        ]

        total_deleted = 0

        for pattern in patterns:
            keys = []
            cursor = "0"
            print(f"Scanning for keys matching: {pattern}")

            # Using scan_iter for safety
            for key in r.scan_iter(match=pattern, count=100):
                keys.append(key)

            if keys:
                print(f"  Found {len(keys)} keys. Deleting...")
                # Delete in chunks
                chunk_size = 100
                for i in range(0, len(keys), chunk_size):
                    chunk = keys[i : i + chunk_size]
                    if chunk:
                        r.delete(*chunk)
                total_deleted += len(keys)
                print("  Deleted.")
            else:
                print("  No keys found.")

        print(f"Total keys deleted: {total_deleted}")

    except redis.ConnectionError:
        print(f"Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    clear_cache()
