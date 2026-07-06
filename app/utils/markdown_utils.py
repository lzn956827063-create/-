import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension


def render_markdown(text: str) -> str:
    """Convert Markdown text to HTML with code highlighting, tables, and TOC support."""
    md = markdown.Markdown(
        extensions=[
            CodeHiliteExtension(guess_lang=True, css_class="highlight"),
            FencedCodeExtension(),
            TableExtension(),
            TocExtension(permalink=True, permalink_title="Permalink to this section"),
            "nl2br",
            "sane_lists",
            "smarty",
        ],
        output_format="html5",
    )
    return md.convert(text)


def extract_excerpt(markdown_text: str, html_text: str = None, max_chars: int = 300) -> str:
    """Extract a plain-text excerpt from Markdown content."""
    import re

    if html_text:
        # Strip HTML tags for plain text excerpt
        plain = re.sub(r"<[^>]+>", "", html_text)
    else:
        # Strip markdown syntax roughly
        plain = re.sub(r"[#*`~\[\]()!_>|-]", " ", markdown_text)
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= max_chars:
        return plain
    return plain[:max_chars].rsplit(" ", 1)[0] + "..."
