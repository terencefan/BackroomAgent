import os
import sys

# Ensure the project root is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from textwrap import dedent

from backroom_agent.graph import run_once


async def run_demo(user_input: str = None):
    print("--- Starting Agent Test ---")
    query = user_input or "Hello, Backrooms Entity! What is your name?"
    print(f"User: {query}")

    try:
        response = await run_once(query)
        print(f"Agent: {response.content}")
        print("\n--- Test Passed ✅ ---")
    except Exception as e:
        print(f"\n--- Test Failed ❌ ---")
        print(e)
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="User input message")
    args = parser.parse_args()

    asyncio.run(run_demo(args.input))
