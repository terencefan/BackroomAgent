import os
import time

from backroom_agent.tools.wiki_tools import (convert_html_to_room_json,
                                             fetch_wiki_content,
                                             get_level_name_from_url)


def process_level(level_num):
    url = f"https://backrooms-wiki-cn.wikidot.com/level-{level_num}"

    # Predict filenames
    # We can use get_level_name_from_url for accuracy, though it's likely just level-{num}
    # But let's be safe and aligned with how tools work
    # We need to call get_level_name_from_url before fetching to check existing file
    level_name = f"level-{level_num}"
    # Or strict parsing:
    # level_name = get_level_name_from_url(url) # This is a pure string function, safe to call.

    html_path = f"data/level/{level_name}.html"
    json_path = f"data/level/{level_name}.json"

    print(f"Processing {level_name}...")

    # 1. Read existing HTML if present
    existing_content = None
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

    # 2. Fetch (this saves the new HTML file)
    try:
        content, fetched_level_name, _ = fetch_wiki_content(url)
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    # Verify our name prediction matched
    if fetched_level_name != level_name:
        print(
            f"Warning: URL {url} resolved to name {fetched_level_name} instead of {level_name}"
        )
        level_name = fetched_level_name

    # 3. Check for content changes
    content_changed = True  # Force update because prompt changed
    # if existing_content and existing_content == content:
    #     content_changed = False
    #     print(f"  Content for {level_name} has not changed.")
    # else:
    #     print(f"  Content for {level_name} has changed (or is new).")

    # 4. Convert if needed
    # We force conversion if content changed.
    # If content NOT changed, but JSON is missing, we also need to convert.
    json_path = f"data/level/{level_name}.json"
    should_convert = True  # content_changed or not os.path.exists(json_path)

    if should_convert:
        try:
            convert_html_to_room_json(content, level_name)
            print(f"  Conversion completed for {level_name}.")
        except Exception as e:
            print(f"  Failed to convert {level_name}: {e}")
    else:
        print(f"  JSON for {level_name} is up to date. Skipping conversion.")


def main():
    for i in range(3, 12):  # 3 to 11
        process_level(i)
        time.sleep(1)  # Be nice to the server


if __name__ == "__main__":
    main()
