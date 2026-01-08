from backroom_agent.tools.wiki_tools import fetch_wiki_content, convert_html_to_room_json
import os
import argparse

def test_fetch():
    parser = argparse.ArgumentParser(description="Test Wiki Tool")
    parser.add_argument("--force", action="store_true", help="Force regeneration of JSON")
    args = parser.parse_args()

    # 1. Prepare Check
    # We need to know the level name beforehand to read the existing file, 
    # but level_name is derived from URL. Let's assume we can get it or just use the tool.
    # Actually, fetch_wiki_content overwrites the file. 
    # To properly test caching, we should read the file AFTER fetch (which is what we did),
    # BUT we need to realize `fetch_wiki_content` *just* overwrote it.
    
    # Correct Logic:
    # 1. Get existing content (if any)
    # 2. Fetch new content (don't save yet? or save always?)
    # The tool `fetch_wiki_content` SAVES automatically.
    
    # Let's import get_level_name_from_url to predict the path
    from backroom_agent.tools.wiki_tools import get_level_name_from_url
    url = "https://backrooms-wiki-cn.wikidot.com/level-1"
    level_name_prediction = get_level_name_from_url(url)
    html_path = f"data/level/{level_name_prediction}.html"
    
    existing_content = None
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
            
    print(f"Fetching {url}...")
    content, level_name = fetch_wiki_content(url)
    print(f"Content length: {len(content)}, Level Name: {level_name}")
    
    # Check if HTML content has changed
    content_changed = True
    if existing_content and existing_content == content:
        content_changed = False
        print(f"Content for {level_name} has not changed.")
    else:
        print(f"Content for {level_name} has changed (or is new).")
    
    # Check if we should skip conversion
    # Skip if: NOT force AND content hasn't changed AND json exists
    json_path = f"data/level/{level_name}.json"
    if not args.force and not content_changed and os.path.exists(json_path):
        print(f"JSON for {level_name} is up to date. Skipping conversion.")
        return

    # 2. Convert
    print("Converting to JSON...")
    json_result = convert_html_to_room_json(content, level_name)
    print("JSON Result Preview:")
    print(json_result[:500])
    
    # Save JSON for inspection
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_result)
    print(f"Saved JSON to {json_path}")

if __name__ == "__main__":
    test_fetch()
