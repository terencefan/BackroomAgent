import os
import json
import logging
from typing import Dict, Any, List
from urllib.parse import urlparse
from backroom_agent.utils.common import get_project_root
from backroom_agent.tools.wiki_tools import fetch_wiki_content, get_level_name_from_url
from backroom_agent.utils.vector_store import search_similar_items, rebuild_vector_db, update_vector_db
from backroom_agent.utils.search import search_backrooms_wiki
from .state import LevelAgentState

logger = logging.getLogger(__name__)

def resolve_url_node(state: LevelAgentState):
    """
    Check if the input is a valid Backrooms URL. If not, search for it.
    Also initializes state flags.
    """
    url = state.get("url")
    level_name = state.get("level_name")
    logs = state.get("logs", [])
    
    # Initialize flags
    state_updates = {
        "items_extracted": False,
        "entities_extracted": False
    }
    
    # Allowed domains
    target_domains = ["backrooms-wiki-cn.wikidot.com", "brcn.backroomswiki.cn"]

    # 1. Check if we already have a URL
    if url:
        parsed = urlparse(url)
        if any(domain in parsed.netloc for domain in target_domains):
            logs.append(f"Valid URL provided: {url}")
            state_updates["logs"] = logs
            return state_updates
        else:

            # URL provided but not in allowed list? 
            # It might be a search term passed as URL or just an external link.
            # If it's not a URL structure at all, treat as search term.
            if not parsed.scheme:
                # User likely passed "Level 1" into the url field
                logs.append(f"Input '{url}' is not a URL. Using as search query.")
                level_name = url # Treat input as level name query
                url = None
            else:
                logs.append(f"Warning: URL {url} is not from allowed domains. Attempting to use anyway or search.")
    
    # 2. Check for local file first to avoid unnecessary search
    if not url and level_name:
        root = get_project_root()
        # Try both original and normalized name
        candidates = [level_name, level_name.lower().replace(" ", "-")]
        for cand in candidates:
            html_path = os.path.join(root, "data/level", f"{cand}.html")
            if os.path.exists(html_path):
                logs.append(f"Found local file for {level_name} at {html_path}. Skipping search.")
                state_updates["logs"] = logs
                state_updates["level_name"] = cand
                return state_updates

    # 3. If no valid URL and no local file, search using level_name
    if not url and level_name:
        logs.append(f"Searching for wiki page: {level_name}")
        found_url = search_backrooms_wiki(level_name)
        if found_url:
            logs.append(f"Found URL: {found_url}")
            state_updates["logs"] = logs
            state_updates["url"] = found_url
            return state_updates
        else:
             logs.append(f"Search failed for: {level_name}")
             
    state_updates["logs"] = logs
    return state_updates

def fetch_content_node(state: LevelAgentState):
    """
    Fetches HTML content from URL or local file.
    """
    url = state.get("url")
    level_name = state.get("level_name")
    logs = state.get("logs", [])
    
    html_content = ""
    
    # 1. Determine Level Name
    if not level_name and url:
        level_name = get_level_name_from_url(url)
    
    if not level_name:
        return {"logs": logs + ["Error: Could not determine level name."]}

    # 2. Check Local File first if not forcing update
    root = get_project_root()
    html_path = os.path.join(root, "data/level", f"{level_name}.html")
    
    if os.path.exists(html_path) and not state.get("force_update") and not url:
        # Load local
        logs.append(f"Loading local HTML for {level_name}")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    elif url:
        # Fetch remote
        # We reuse the existing tool logic which saves to file automatically
        logs.append(f"Fetching remote content from {url}")
        content, extracted_name = fetch_wiki_content(url, save_files=True)
        html_content = content
        if not level_name: 
            level_name = extracted_name # Update if we didn't have it
    else:
        # If still no URL here (search failed in previous node), use local check or fail
        msg = f"No URL provided and search failed for {level_name}"
        logs.append(msg)
        # Try local fallback one last time even without force check
        if os.path.exists(html_path):
             logs.append(f"Fallback: Loading local HTML for {level_name}")
             with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        else:
             return {"logs": logs + [f"Error: {msg}"]}

    return {
        "html_content": html_content, 
        "level_name": level_name,
        "url": url,
        "logs": logs
    }





def filter_items_node(state: LevelAgentState):
    """
    Filters extracted items based on:
    1. Vector DB similarity (Dedup).
    2. Hallucination check (String matching in source).
    """
    raw_items = state.get("extracted_items_raw", [])
    html_content = state.get("html_content", "")
    logs = state.get("logs", [])
    
    final_items = []
    
    logs.append("Filtering items...")
    
    # Threshold for vector similarity to consider it "already exists"
    # If similarity > threshold, we count it as a duplicate
    SIMILARITY_THRESHOLD = 0.85 

    total_items = len(raw_items)
    for i, item in enumerate(raw_items):
        name = item.get("name")
        description = item.get("description", "")
        
        logs.append(f"Processing item {i+1}/{total_items}: {name}")
        
        # 1. Hallucination Check (Basic)
        # Check if the name (or part of it) actually appears in the text
        if name not in html_content:
            logs.append(f"Filtered (Hallucination): '{name}' not found in source text.")
            continue
            
        # 2. Vector DB Check
        # Let's search by name primarily as that's the main identifier
        query = name 
        
        existing_matches = search_similar_items(query, k=1)
        
        is_duplicate = False
        if existing_matches:
            top_match = existing_matches[0]
            score = top_match['score']
            existing_name = top_match['metadata']['name']
            
            if score > SIMILARITY_THRESHOLD:
                is_duplicate = True
                logs.append(f"Filtered (Duplicate): '{name}' is too similar to existing '{existing_name}' (Score: {score:.4f})")
        
        if not is_duplicate:
            final_items.append(item)
            logs.append(f"Accepted: {name}")

    return {"final_items": final_items, "logs": logs, "items_extracted": True}

def filter_entities_node(state: LevelAgentState):
    """
    Filters extracted entities based on:
    1. Hallucination check.
    2. Optional: Vector DB similarity (Dedup) - currently reusing item vector store for checking.
    """
    raw_entities = state.get("extracted_entities_raw", [])
    html_content = state.get("html_content", "")
    logs = state.get("logs", [])
    
    final_entities = []
    
    logs.append("Filtering entities...")
    
    SIMILARITY_THRESHOLD = 0.85 

    total = len(raw_entities)
    for i, entity in enumerate(raw_entities):
        name = entity.get("name")
        
        logs.append(f"Processing entity {i+1}/{total}: {name}")
        
        # 1. Hallucination Check
        if name not in html_content:
            logs.append(f"Filtered (Hallucination): '{name}' not found in source text.")
            continue
            
        # 2. Vector DB Check (Using item store temporarily or same unified store)
        # Assuming we might want to check against items too (don't want item == entity)
        # But really we want an entity DB. For now, strict duplicates are fine.
        # We will implement separate check if needed.
        
        final_entities.append(entity)
        logs.append(f"Accepted: {name}")

    return {"final_entities": final_entities, "logs": logs, "entities_extracted": True}

def check_completion_node(state: LevelAgentState):
    """
    Dummy/Barrier node to synchronize execution.
    It doesn't change state, just passes through.
    """
    return {}

def update_level_json_node(state: LevelAgentState):
    """
    Updates the Level JSON with the extracted and filtered items AND entities.
    """
    level_name = state.get("level_name")
    final_items = state.get("final_items", [])
    final_entities = state.get("final_entities", [])
    logs = state.get("logs", [])
    
    if not level_name:
        return {"logs": logs}

    root = get_project_root()
    json_path = os.path.join(root, "data/level", f"{level_name}.json")
    
    if not os.path.exists(json_path):
        logs.append(f"Warning: JSON file {json_path} not found. Cannot update items.")
        return {"logs": logs}
        
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        data["findable_items"] = final_items
        data["entities"] = final_entities
        
        # Remove old key if it exists to keep it clean
        if "items" in data:
            del data["items"]
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logs.append(f"Updated level JSON: {json_path}")

        # --- Save Individual Item Files ---
        item_base_dir = os.path.join(root, "data/item")
        saved_items_count = 0
        saved_item_paths = []
        for item in final_items:
            try:
                cat = item.get("category", "Uncategorized")
                iid = item.get("id", "unknown")
                item_dir = os.path.join(item_base_dir, cat)
                os.makedirs(item_dir, exist_ok=True)
                
                item_path = os.path.join(item_dir, f"{iid}.json")
                with open(item_path, 'w', encoding='utf-8') as f:
                    json.dump(item, f, ensure_ascii=False, indent=2)
                saved_items_count += 1
                saved_item_paths.append(item_path)
            except Exception as e:
                logs.append(f"Error saving item {item.get('name')}: {e}")
        
        # --- Save Individual Entity Files ---
        entity_base_dir = os.path.join(root, "data/entity")
        saved_entities_count = 0
        saved_entity_paths = []
        for entity in final_entities:
            try:
                # Entities generally don't have sub-categories like items, or rely on behavior
                # Simple structure: data/entity/{id}.json
                eid = entity.get("id", "unknown")
                os.makedirs(entity_base_dir, exist_ok=True)
                
                entity_path = os.path.join(entity_base_dir, f"{eid}.json")
                with open(entity_path, 'w', encoding='utf-8') as f:
                    json.dump(entity, f, ensure_ascii=False, indent=2)
                saved_entities_count += 1
                saved_entity_paths.append(entity_path)
            except Exception as e:
                logs.append(f"Error saving entity {entity.get('name')}: {e}")

        logs.append(f"Saved {saved_items_count} item files and {saved_entities_count} entity files.")

        # --- Update Vector Stores ---
        try:
            # 1. Update Item Vector Store
            item_db_path = os.path.join(root, "data/vector_store/item_vector_store.pkl")
            if os.path.exists(item_db_path) and saved_item_paths:
                logs.append(f"Updating Item Vector Store incrementally with {len(saved_item_paths)} items...")
                update_vector_db(file_paths=saved_item_paths, db_path=item_db_path)
            else:
                logs.append("Rebuilding Item Vector Store (Full)...")
                rebuild_vector_db(item_dir=item_base_dir, db_path=item_db_path)
            
            # 2. Update Entity Vector Store
            entity_db_path = os.path.join(root, "data/vector_store/entity_vector_store.pkl")
            if os.path.exists(entity_db_path) and saved_entity_paths:
                logs.append(f"Updating Entity Vector Store incrementally with {len(saved_entity_paths)} entities...")
                update_vector_db(file_paths=saved_entity_paths, db_path=entity_db_path)
            else:
                logs.append("Rebuilding Entity Vector Store (Full)...")
                rebuild_vector_db(item_dir=entity_base_dir, db_path=entity_db_path)
            
            logs.append("Vector stores updated successfully.")
        except Exception as e:
            logs.append(f"Error updating vector stores: {e}")
            
    except Exception as e:
        logs.append(f"Error updating JSON/Files: {str(e)}")
        
    return {"logs": logs}
