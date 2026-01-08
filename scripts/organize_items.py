import os
import json
import shutil
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backroom_agent.utils.common import get_project_root

def organize_items():
    root = get_project_root()
    item_dir = os.path.join(root, "data/item")
    
    if not os.path.exists(item_dir):
        print(f"Directory not found: {item_dir}")
        return

    print(f"Organizing items in {item_dir}...")
    
    # List all files in item_dir
    files = os.listdir(item_dir)
    count = 0
    
    for filename in files:
        if not filename.endswith(".json"):
            continue
            
        file_path = os.path.join(item_dir, filename)
        
        # Skip if it's a directory
        if os.path.isdir(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            category = data.get("category", "General")
            
            # Simple sanitization for folder name
            # Capitalize first letter
            category = category.strip().title()
            # Remove unsafe chars if any (basic check)
            safe_category = "".join([c for c in category if c.isalnum() or c in (' ', '_', '-')])
            
            if not safe_category:
                safe_category = "General"
                
            # Target directory
            category_path = os.path.join(item_dir, safe_category)
            os.makedirs(category_path, exist_ok=True)
            
            # Move file
            new_path = os.path.join(category_path, filename)
            shutil.move(file_path, new_path)
            count += 1
            # print(f"Moved {filename} -> {safe_category}/{filename}")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    print(f"Successfully organized {count} items.")

if __name__ == "__main__":
    organize_items()
