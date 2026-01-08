import sys
import os

# Create a dummy test to verify the function import and logic
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backroom_agent.utils.search import search_backrooms_wiki

def main():
    query = "Level 1"
    print(f"Searching for: {query}")
    url = search_backrooms_wiki(query)
    print(f"Result URL: {url}")

if __name__ == "__main__":
    main()
