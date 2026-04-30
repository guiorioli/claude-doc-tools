from __future__ import annotations

from pathlib import Path
from typing import List


def convert_html(path: Path, image_dir: Path) -> tuple[str, List[Path]]:
    from bs4 import BeautifulSoup

    raw = path.read_bytes()
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    parts: List[str] = []
    if soup.title and soup.title.string:
        parts.append(f"# {soup.title.string.strip()}\n")

    body = soup.body or soup
    parts.append(body.get_text("\n", strip=True))
    return "\n".join(parts), []


def convert_rtf(path: Path, image_dir: Path) -> tuple[str, List[Path]]:
    from striprtf.striprtf import rtf_to_text

    text = rtf_to_text(path.read_text(encoding="utf-8", errors="ignore"))
    return text, []
