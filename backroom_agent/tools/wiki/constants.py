# Request Headers
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://backrooms-wiki-cn.wikidot.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
}

# Tags to remove completely
UNWANTED_TAGS = [
    "script", "style", "meta", "link", "noscript", "iframe",
    "svg", "form", "input", "button", "nav", "footer", "header", "aside",
]

# Classes/IDs indicating garbage content
GARBAGE_CLASSES = [
    "sidebar", "ad", "advertisement", "cookie", "popup", "newsletter",
    "menu", "navigation", "social", "share", "creditRate", "credit",
    "modalbox", "printuser", "licensebox", "rate-box",
    "page-options-bottom", "bottom-box", "page-tags",
    "page-info", "page-info-break", "top-text", "bottom-text",
]

# Tags to keep (others are unwrapped)
USEFUL_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "br", "hr",
    "ul", "ol", "li",
    "dl", "dt", "dd",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td",
    "blockquote", "pre", "code",
    "b", "strong", "i", "em", "u", "a",
}

# IDs/Classes indicating main content
MAIN_CONTENT_IDS = [
    "main-content", "page-content", "content",
    "mw-content-text", "wiki-content",
]

MAIN_CONTENT_CLASSES = [
    "mw-parser-output", "main-content",
    "post-content", "entry-content",
]
