import os
import sys
from pprint import pprint

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backroom_agent.subagents.event import event_agent
from backroom_agent.utils.item import Item


def run_subagent_test():
    print("--- Running Event SubAgent ---")

    # We use a level that should exist or be fetched
    level_name = "level-2"

    initial_state = {
        "level_name": level_name,
        "user_input": "我尝试搜寻一些补给",
        "level_context": "",
        "events": [],
        "items": [],
        "error_message": "",
        "retry_count": 0,
    }

    try:
        result = event_agent.invoke(initial_state)

        print("\n--- Final Result ---")
        if result.get("error_message"):
            print(f"FAILED with error: {result['error_message']}")
        else:
            print(f"SUCCESS! Generated {len(result['events'])} events.")
            for evt in result["events"]:
                print(f"Event: {evt.name} ({evt.die_type})")
                print(evt.to_json())

    except Exception as e:
        print(f"Execution Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_subagent_test()
