from __future__ import annotations

import zipfile
from pathlib import Path
from typing import List


def convert_odt(path: Path, image_dir: Path) -> tuple[str, List[Path]]:
    from odf.opendocument import load
    from odf.text import P, H

    doc = load(str(path))
    parts: List[str] = []

    def walk(node):
        tag = getattr(node, "qname", (None, None))[1]
        if tag == "h":
            level = int(node.getAttribute("outlinelevel") or 1)
            parts.append(f"{'#' * min(level, 6)} {_text(node)}")
        elif tag == "p":
            text = _text(node)
            if text:
                parts.append(text)
        else:
            for child in node.childNodes:
                walk(child)

    walk(doc.body)

    images = _extract_embedded_images(path, image_dir)
    return "\n\n".join(parts), images


def convert_ods(path: Path, image_dir: Path) -> tuple[str, List[Path]]:
    from odf.opendocument import load
    from odf.table import Table, TableRow, TableCell

    doc = load(str(path))
    parts: List[str] = []

    for table in doc.getElementsByType(Table):
        name = table.getAttribute("name") or "Sheet"
        parts.append(f"## Sheet: {name}\n")
        rows: List[List[str]] = []
        for row in table.getElementsByType(TableRow):
            cells: List[str] = []
            for cell in row.getElementsByType(TableCell):
                repeat = int(cell.getAttribute("numbercolumnsrepeated") or 1)
                value = _text(cell)
                cells.extend([value] * repeat)
            rows.append(cells)

        rows = [r for r in rows if any(c.strip() for c in r)]
        if not rows:
            parts.append("_(empty)_\n")
            continue

        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        header = rows[0]
        body = rows[1:] if len(rows) > 1 else []
        parts.append("| " + " | ".join(header) + " |")
        parts.append("| " + " | ".join(["---"] * width) + " |")
        for r in body:
            parts.append("| " + " | ".join(r) + " |")
        parts.append("")

    images = _extract_embedded_images(path, image_dir)
    return "\n".join(parts), images


def convert_odp(path: Path, image_dir: Path) -> tuple[str, List[Path]]:
    from odf.opendocument import load
    from odf.draw import Page

    doc = load(str(path))
    parts: List[str] = []
    for idx, page in enumerate(doc.getElementsByType(Page), start=1):
        parts.append(f"## Slide {idx}\n")
        text = _text(page)
        if text:
            parts.append(text)
        parts.append("")

    images = _extract_embedded_images(path, image_dir)
    return "\n".join(parts), images


def _text(node) -> str:
    chunks: List[str] = []
    for child in node.childNodes:
        if child.nodeType == 3:
            chunks.append(child.data)
        else:
            chunks.append(_text(child))
    return "".join(chunks).strip()


def _extract_embedded_images(path: Path, image_dir: Path) -> List[Path]:
    saved: List[Path] = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if name.startswith("Pictures/") and not name.endswith("/"):
                out = image_dir / Path(name).name
                with zf.open(name) as src, open(out, "wb") as dst:
                    dst.write(src.read())
                saved.append(out)
    return saved
