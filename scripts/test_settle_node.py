import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.messages import AIMessage, HumanMessage

from backroom_agent.nodes.settle import settle_node
from backroom_agent.protocol import DiceRoll
from backroom_agent.state import State


def test_settle_node():
    print("--- Testing Settle Node (Standalone) ---")

    # Mock Game State
    from backroom_agent.protocol import Attributes, GameState, Vitals

    mock_state = GameState(
        level="Level 0",
        attributes=Attributes(STR=10, DEX=10, CON=10, INT=10, WIS=10, CHA=10),
        vitals=Vitals(hp=8, maxHp=10, sanity=90),
        inventory=[],
    )

    # Case 1: Simple Narrative, No Dice
    print("\n[Case 1] Narrative only, no dice. (HP:8, Sanity:90)")
    state_no_dice = State(
        current_game_state=mock_state,
        messages=[AIMessage(content="You trip and fall on the carpet.")],
        dice_roll=None,
        level_context="Level 0: Monochromatic yellow wallpaper. Hum-buzz.",
        # minimal other fields
    )

    try:
        result = settle_node(state_no_dice, config={})
        print("Input: 'You trip and fall on the carpet.'")
        print(f"Output: {result.get('messages')[0].content}")
        new_gs = result.get("current_game_state")
        print(f"New State: HP={new_gs.vitals.hp}, Sanity={new_gs.vitals.sanity}")
    except Exception as e:
        print(f"Error in Case 1: {e}")

    # Case 2: Narrative with Dice Roll
    print("\n[Case 2] Combat! (d20=2, Fail).")
    # Simulate Dice Node having added a message
    dice_msg = HumanMessage(content="Dice Roll Result: [D20] 2. Reason: Fight.")

    state_with_dice = State(
        current_game_state=mock_state,
        messages=[AIMessage(content="You try to fight the hound."), dice_msg],
        dice_roll=DiceRoll(type="d20", result=2, reason="Attack"),
        level_context="Level 0: Danger nearby.",
    )

    try:
        result = settle_node(state_with_dice, config={})
        print("Input: 'You try to fight the hound.' + Dice(d20=2)")
        print(f"Output: {result.get('messages')[0].content}")
        new_gs = result.get("current_game_state")
        print(f"New State: HP={new_gs.vitals.hp}, Sanity={new_gs.vitals.sanity}")
    except Exception as e:
        print(f"Error in Case 2: {e}")

    # Case 3: History Filtering + Multiple Narrative Chunks
    print("\n[Case 3] Complex History (Should ignore old messages).")

    # Old history
    msg_history = [
        AIMessage(content="Welcome to the Backrooms."),
        HumanMessage(content="I look around."),
        AIMessage(content="Yellow wallpaper everywhere."),
        HumanMessage(content="I kick the wall."),
    ]

    # Current Interaction
    current_msgs = [
        AIMessage(content="You try to kick the wall hard to break through."),
        HumanMessage(
            content="Dice Roll Result: [D20] 18. Reason: Break Wall. Outcome: You create a hole."
        ),
        HumanMessage(
            content="System Note: The noise attracts entities."
        ),  # Hypothetical extra system msg
    ]

    state_complex = State(
        current_game_state=mock_state,
        messages=msg_history + current_msgs,
        dice_roll=DiceRoll(type="d20", result=18, reason="Break Wall"),
        level_context="Level 0: Monnotony.",
    )

    try:
        result = settle_node(state_complex, config={})
        print("Input History Len:", len(msg_history + current_msgs))
        # Internally Settle Node should only see the last 3 messages
        print(f"Output: {result.get('messages')[0].content}")
        new_gs = result.get("current_game_state")
        # Maybe no HP change, but sanity change? or items?
        print(f"New State: HP={new_gs.vitals.hp}, Sanity={new_gs.vitals.sanity}")
    except Exception as e:
        print(f"Error in Case 3: {e}")


if __name__ == "__main__":
    test_settle_node()
