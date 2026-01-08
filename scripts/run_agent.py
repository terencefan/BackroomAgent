import os
import sys

# Ensure the project root is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from textwrap import dedent

from backroom_agent.graph import run_once


def run_demo():
    print("--- Starting Agent Test ---")
    query = "Hello, Backrooms Entity! What is your name?"
    print(f"User: {query}")

    try:
        response = run_once(query)
        print(f"Agent: {response.content}")
        print("\n--- Test Passed ✅ ---")
    except Exception as e:
        print(f"\n--- Test Failed ❌ ---")
        print(e)
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_demo()
