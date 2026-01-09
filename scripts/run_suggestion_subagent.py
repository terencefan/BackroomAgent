import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from backroom_agent.state import State
from backroom_agent.subagents.suggestion import suggestion_agent
from backroom_agent.utils.item import Item


def run_suggestion_test():
    print("--- Running Suggestion SubAgent ---")

    level_name = "level-1"

    # Test case 1: Basic
    print("\n[Test 1] Walking down corridor, no items")
    state_1 = cast(
        State,
        {
            "level_name": level_name,
            "user_input": "I am walking down a long corridor.",
            "level_context": "",
            "items": [],
            "suggestions": [],
        },
    )
    result_1 = suggestion_agent.invoke(state_1)
    print("Suggestions:", result_1["suggestions"])

    # Test case 2: With specific item in inventory
    print("\n[Test 2] Encountered entity, owning a weapon")
    state_2 = cast(
        State,
        {
            "level_name": level_name,
            "user_input": "Found a hound nearby.",
            "level_context": "",
            "items": [
                Item(name="Fire Axe", quantity=1),
                Item(name="Almond Water", quantity=1),
            ],
            "suggestions": [],
        },
    )
    result_2 = suggestion_agent.invoke(state_2)
    print("Suggestions:", result_2["suggestions"])


if __name__ == "__main__":
    run_suggestion_test()
