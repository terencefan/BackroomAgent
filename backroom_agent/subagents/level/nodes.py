import os
import json
import logging
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from urllib.parse import urlparse
from backroom_agent.utils.common import get_project_root, load_prompt, get_llm
from backroom_agent.tools.wiki_tools import fetch_wiki_content, convert_html_to_room_json, get_level_name_from_url
from backroom_agent.utils.vector_store import search_similar_items
from backroom_agent.utils.search import search_backrooms_wiki
from .state import LevelAgentState

logger = logging.getLogger(__name__)

def resolve_url_node(state: LevelAgentState):
    """
    Check if the input is a valid Backrooms URL. If not, search for it.
    """
    url = state.get("url")
    level_name = state.get("level_name")
    logs = state.get("logs", [])
    
    # Allowed domains
    target_domains = ["backrooms-wiki-cn.wikidot.com", "brcn.backroomswiki.cn"]

    # 1. Check if we already have a URL
    if url:
        parsed = urlparse(url)
        if any(domain in parsed.netloc for domain in target_domains):
            logs.append(f"Valid URL provided: {url}")
            return {"logs": logs}
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
                return {"logs": logs, "level_name": cand}

    # 3. If no valid URL and no local file, search using level_name
    if not url and level_name:
        logs.append(f"Searching for wiki page: {level_name}")
        found_url = search_backrooms_wiki(level_name)
        if found_url:
            logs.append(f"Found URL: {found_url}")
            return {"url": found_url, "logs": logs}
        else:
             logs.append(f"Search failed for: {level_name}")
             
    return {"logs": logs}

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

def generate_json_node(state: LevelAgentState):
    """
    Generates the Level JSON description from HTML.
    """
    html_content = state.get("html_content")
    level_name = state.get("level_name")
    logs = state.get("logs", [])

    if not html_content:
        return {"logs": logs + ["Skipping JSON generation: No HTML content."]}

    # Check if JSON already exists
    root = get_project_root()
    json_path = os.path.join(root, "data/level", f"{level_name}.json")
    
    if os.path.exists(json_path) and not state.get("force_update"):
        logs.append(f"JSON already exists at {json_path}. Skipping generation.")
        return {"level_json_generated": True, "logs": logs}

    logs.append("Generating Level JSON from HTML...")
    try:
        # This function saves the file internally
        convert_html_to_room_json(html_content, level_name)
        logs.append(f"Successfully generated and saved {json_path}")
        return {"level_json_generated": True, "logs": logs}
    except Exception as e:
        logs.append(f"Error generating JSON: {str(e)}")
        return {"level_json_generated": False, "logs": logs}

def extract_items_node(state: LevelAgentState):
    """
    Extracts potential items from the HTML content using LLM.
    """
    html_content = state.get("html_content")
    logs = state.get("logs", [])
    
    if not html_content:
        return {"extracted_items_raw": [], "logs": logs}

    logs.append("Extracting items from HTML...")
    
    llm = get_llm()
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "level_agent.prompt")
    system_prompt = load_prompt(prompt_path)
    
    # We might want to truncate HTML if it's too long, but usually wiki pages are okay for recent models
    messages = [
        SystemMessage(content=system_prompt.format(context=html_content)),
        HumanMessage(content="Extract the items now in JSON format.")
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content
        
        # Parse JSON from Markdown block
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        items = json.loads(content)
        logs.append(f"Extracted {len(items)} raw items.")
        return {"extracted_items_raw": items, "logs": logs}
        
    except Exception as e:
        logs.append(f"Error extracting items: {e}")
        return {"extracted_items_raw": [], "logs": logs}

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

    for item in raw_items:
        name = item.get("name")
        description = item.get("description", "")
        
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

    return {"final_items": final_items, "logs": logs}

def update_level_json_node(state: LevelAgentState):
    """
    Updates the Level JSON with the extracted and filtered items.
    """
    level_name = state.get("level_name")
    final_items = state.get("final_items", [])
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
            
        data["items"] = final_items
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logs.append(f"Updated {json_path} with {len(final_items)} items.")
        
    except Exception as e:
        logs.append(f"Error updating JSON with items: {str(e)}")
        
    return {"logs": logs}
