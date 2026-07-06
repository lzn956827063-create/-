import bleach

# Allowed HTML tags for user-generated content (comments, etc.)
ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "ul",
    "br",
    "span",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "span": ["class"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(text: str) -> str:
    """Strip all potentially dangerous HTML from user input."""
    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


def sanitize_plain_text(text: str) -> str:
    """Strip ALL HTML tags, returning only plain text."""
    return bleach.clean(text, tags=[], attributes={}, strip=True)
