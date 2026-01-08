import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from langchain_core.messages import SystemMessage, HumanMessage
from backroom_agent.utils.common import get_project_root, load_prompt, get_llm

def convert_html_to_room_json(html_content: str, level_name: str) -> str:
    """
    Converts cleaned HTML content to a Game Context JSON using an LLM.
    
    Args:
        html_content (str): The cleaned HTML content.
        level_name (str): The name/ID of the level for saving the file.
        
    Returns:
        str: A JSON string representing the game context.
    """
    root_dir = get_project_root()
    json_path = os.path.join(root_dir, "data/level", f"{level_name}.json")
    
    llm = get_llm()
    system_prompt_text = load_prompt("convert_html_to_room_json.md")
    
    messages = [
        SystemMessage(content=system_prompt_text),
        HumanMessage(content=f"Here is the cleaned HTML content of the level:\n\n{html_content}")
    ]
    
    # We can try to use standard invoke. The prompt asks for a Markdown code block with JSON.
    response = llm.invoke(messages)
    content = response.content
    
    # Helper to clean up markdown code blocks if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].strip()
        
    # Save the generated JSON
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return content

def get_level_name_from_url(url: str) -> str:
    """Extracts the level name from the URL."""
    path = urlparse(url).path
    return path.strip("/").split("/")[-1]

def save_to_file(content: str, directory: str, filename: str):
    """Saves content to a file in the specified directory."""
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath

def fetch_wiki_content(url: str, save_files: bool = True) -> str:
    """
    Fetches the content of a URL and cleans it, keeping only useful tags.
    Saves raw content to data/raw and cleaned content to data/level.
    
    Args:
        url (str): The URL to fetch.
        save_files (bool): Whether to save the raw and cleaned content to files.
        
    Returns:
        str: The cleaned HTML content string.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        raw_content = response.text
    except requests.RequestException as e:
        return f"Error fetching URL: {str(e)}"

    level_name = get_level_name_from_url(url)
    
    if save_files:
        root_dir = get_project_root()
        save_to_file(raw_content, os.path.join(root_dir, "data/raw"), f"{level_name}.html")

    soup = BeautifulSoup(response.content, 'html.parser')

    # Remove unwanted tags completely (structure and content)
    for tag in soup(["script", "style", "meta", "link", "noscript", "iframe", "svg", "form", "input", "button", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Remove elements by class/id that are clearly garbage (heuristic)
    garbage_classes = [
        'sidebar', 'ad', 'advertisement', 'cookie', 'popup', 'newsletter', 
        'menu', 'navigation', 'social', 'share', 'creditRate', 'credit', 
        'modalbox', 'printuser', 'licensebox', 'rate-box', 'page-options-bottom',
        'bottom-box', 'page-tags', 'page-info', 'page-info-break',
        'top-text', 'bottom-text'
    ]
    
    for tag in soup.find_all(True):
        if not tag.name:
            continue
            
        # check for inline style display: none
        style = tag.get('style', '')
        if style and 'display:none' in style.lower().replace(' ', ''): # handle spaces like 'display:none' or 'display: none'
             tag.decompose()
             continue
        
        # check class
        classes = tag.get('class', [])
        if classes and any(garbage in ' '.join(classes).lower() for garbage in garbage_classes):
             tag.decompose()
             continue
        # check id
        id_ = tag.get('id', '')
        if id_ and any(garbage in id_.lower() for garbage in garbage_classes):
             tag.decompose()
             continue

    # Define useful tags to keep AS TAGS. Others will be unwrapped (content kept, tags removed).
    useful_tags = {
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
        'p', 'br', 'hr',
        'ul', 'ol', 'li', 'dl', 'dt', 'dd',
        'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
        'blockquote', 'pre', 'code',
        'b', 'strong', 'i', 'em', 'u', 'a'
    }

    # Identify the main content area to reduce noise if possible
    # Common main content containers
    main_content = None
    possible_ids = ['main-content', 'page-content', 'content', 'mw-content-text', 'wiki-content']
    possible_classes = ['mw-parser-output', 'main-content', 'post-content', 'entry-content']
    
    for pid in possible_ids:
        found = soup.find(id=pid)
        if found:
            main_content = found
            break
            
    if not main_content:
        for pcls in possible_classes:
            found = soup.find(class_=pcls)
            if found:
                main_content = found
                break
    
    # If we found a main content area, use it. Otherwise use the body or whole soup.
    target = main_content if main_content else (soup.body if soup.body else soup)

    # Clean the target
    for tag in target.find_all(True):
        if tag.name not in useful_tags:
            tag.unwrap()
        else:
            # Clean attributes - remove style, onclick, etc.
            # Keep href for 'a', src for 'img'
            attrs = dict(tag.attrs)
            for attr in attrs:
                if attr not in ['href', 'src', 'alt', 'title']:
                    del tag[attr]

            # Additional check for href to remove javascript links
            if tag.name == 'a' and 'href' in tag.attrs:
                href = tag['href'].lower().strip()
                if href.startswith('javascript:') or href == '#':
                    tag.unwrap() # Removes the anchor but keeps text

    # Final cleanup: Remove empty tags
    for tag in target.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
         if not tag.get_text(strip=True):
             tag.decompose()

    # Normalize whitespace in text nodes
    for text in target.find_all(string=True):
        if text.parent.name not in ['pre', 'code']:
            # Replace multiple whitespace (including newlines) with single space
            new_text = re.sub(r'\s+', ' ', text)
            if len(new_text) < len(text):
                text.replace_with(new_text)

    cleaned_content = str(target)
    
    # Remove empty lines and surrounding whitespace on a line-by-line basis
    # This helps clear up the structural whitespace left behind
    cleaned_content = "\n".join([line.strip() for line in cleaned_content.splitlines() if line.strip()])
    
    if save_files:
        root_dir = get_project_root()
        save_to_file(cleaned_content, os.path.join(root_dir, "data/level"), f"{level_name}.html")

    return cleaned_content, level_name
