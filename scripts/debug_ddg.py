import traceback

from ddgs import DDGS

try:
    with DDGS() as ddgs:
        print("Searching...")
        results = ddgs.text("test", max_results=1)
        print("Results:", results)
except Exception:
    traceback.print_exc()
