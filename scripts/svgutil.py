"""Small SVG helpers. Animation is progressive: the unmarked SVG is the
finished frame, and CSS keyframes only play the intro. Clients that skip
animation, including prefers-reduced-motion, still show the full graphic.
"""

from __future__ import annotations


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def motion_style(rules: str, static: bool) -> str:
    if static:
        return ""
    return (
        "<style><![CDATA[\n"
        f"{rules}\n"
        "@media (prefers-reduced-motion: reduce) {\n"
        "  * { animation: none !important; }\n"
        "}\n"
        "]]></style>"
    )


def document(width: int, height: int, body: str, title: str, desc: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
        f"<title>{esc(title)}</title>\n"
        f"<desc>{esc(desc)}</desc>\n"
        f"{body}\n"
        "</svg>\n"
    )
