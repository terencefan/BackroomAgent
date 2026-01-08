import argparse
import json
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backroom_agent.subagents.level import level_agent

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")


def main():
    parser = argparse.ArgumentParser(
        description="Run Level Agent to fetch, process, and extract items from a Level."
    )
    parser.add_argument(
        "url_or_name",
        nargs="?",
        help="URL of the wiki page OR local level name (e.g., 'level-1')",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration of JSON and re-extraction of items",
    )

    args = parser.parse_args()

    # Input handling
    target = args.url_or_name
    if not target:
        # Default for testing
        target = "https://backrooms-wiki-cn.wikidot.com/level-1"
        print(f"No argument provided. Using default test target: {target}")

    initial_state = {"force_update": args.force, "logs": []}

    if target.startswith("http"):
        initial_state["url"] = target
        initial_state["level_name"] = None  # Will be auto-determined
    else:
        initial_state["url"] = None
        initial_state["level_name"] = target

    print(f"--- Starting Level Agent for: {target} ---")

    # Run the graph
    result = level_agent.invoke(initial_state)

    # Output results
    print("\n--- Execution Logs ---")
    for log in result.get("logs", []):
        print(f"[Log] {log}")

    print("\n--- Final Items (Filtered & Verified) ---")
    final_items = result.get("final_items", [])
    if final_items:
        print(json.dumps(final_items, ensure_ascii=False, indent=2))
        print(f"\nTotal items extracted: {len(final_items)}")
    else:
        print("No items found or all were filtered out.")

    # Check for critical errors (no HTML content)
    if not result.get("html_content"):
        print("\n[!] Error: Failed to load HTML content.")
        sys.exit(1)


if __name__ == "__main__":
    main()
