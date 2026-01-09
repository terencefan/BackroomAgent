from typing import List, Tuple, Dict
import re

from bs4 import BeautifulSoup, Tag

from backroom_agent.tools.wiki.constants import (GARBAGE_CLASSES,
                                                 MAIN_CONTENT_CLASSES,
                                                 MAIN_CONTENT_IDS,
                                                 UNWANTED_TAGS, USEFUL_TAGS)


def clean_html_content(raw_html: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Cleans raw HTML using BeautifulSoup, applying filters defined in constants.
    Also extracts all meaningful links.
    Returns: (cleaned_html_string, list_of_links)
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    # 1. Remove unwanted tags (structure and content)
    for tag in soup(UNWANTED_TAGS):
        tag.decompose()

    # 2. Remove garbage by class or ID
    for tag in soup.find_all(True):
        if not tag.name:
            continue

        # Check inline style display: none
        style = tag.get("style", "")
        if style and "display:none" in style.lower().replace(" ", ""):
            tag.decompose()
            continue

        # Check class
        classes = tag.get("class", [])
        if classes and any(
            garbage in " ".join(classes).lower() for garbage in GARBAGE_CLASSES
        ):
            tag.decompose()
            continue

        # Check ID
        id_ = tag.get("id", "")
        if id_ and any(garbage in id_.lower() for garbage in GARBAGE_CLASSES):
            tag.decompose()
            continue

    # 3. Narrow down to main content
    target = _extract_main_content(soup)
    
    # --- Link Extraction Phase ---
    extracted_links = []
    # Find all 'a' tags with href BEFORE we start unwrapping or decomposing empty ones
    # We restrict to 'target' area to avoid sidebar links
    for a_tag in target.find_all("a", href=True):
        href = a_tag["href"].strip()
        text = a_tag.get_text(strip=True)
        if href and not href.startswith("#") and not href.startswith("javascript:"):
            # Filter internal anchor links and JS
            extracted_links.append({"text": text or href, "url": href})

    # 4. Clean tags within target (unwrap non-useful tags, clean attributes)
    for tag in target.find_all(True):
        if tag.name not in USEFUL_TAGS:
            tag.unwrap()
        else:
            _clean_attributes(tag)

    # 5. Remove empty tags
    # Expand list to include formatting and anchors
    tags_to_check = [
        "p", "li", "h1", "h2", "h3", "h4", "h5", "h6", 
        "a", "b", "strong", "i", "em", "u",
        "blockquote", "pre", "code", "div", "span"
    ]
    for tag in target.find_all(tags_to_check):
        if not tag.get_text(strip=True):
            tag.decompose()
            
    # 5b. Remove independent/unpaired useless tags that might have been left over
    # (e.g. <br> or <hr> at start/end or clustered?)
    # Users request: "clean independent unpaired tags".
    # This might mean things like <br> that are not separating text, or empty elements.
    # BS4 'decompose' on empty tags handled most.
    # Let's clean up consecutive <br>s or <hr>s
    # (Optional refinement based on interpretation)

    # 6. Normalize whitespace
    for text in target.find_all(string=True):
        if text.parent.name not in ["pre", "code"]:
            new_text = re.sub(r"\s+", " ", text)
            if len(new_text) < len(text):
                text.replace_with(new_text)

    return str(target).strip(), extracted_links



def _extract_main_content(soup: BeautifulSoup):
    """Identifies the main content area to reduce noise."""
    main_content = None

    for pid in MAIN_CONTENT_IDS:
        found = soup.find(id=pid)
        if found:
            main_content = found
            break

    if not main_content:
        for pcls in MAIN_CONTENT_CLASSES:
            found = soup.find(class_=pcls)
            if found:
                main_content = found
                break

    return main_content if main_content else (soup.body if soup.body else soup)


def _clean_attributes(tag: Tag):
    """Removes unwanted attributes from a tag, keeping only href/src/alt/title."""
    attrs = dict(tag.attrs)
    for attr in attrs:
        if attr not in ["href", "src", "alt", "title"]:
            del tag[attr]

    # Additional check for javascript hrefs
    if tag.name == "a" and "href" in tag.attrs:
        href = tag["href"].lower().strip()
        if href.startswith("javascript:") or href == "#":
            tag.unwrap()
