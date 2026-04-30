from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

# A page is treated as "scanned" when pdfplumber extracts fewer than this many characters.
SCANNED_PAGE_THRESHOLD = 50


def convert_pdf(path: Path, image_dir: Path) -> tuple[str, List[Path]]:
    import pdfplumber

    saved: List[Path] = []
    parts: List[str] = []
    scanned_pages: List[int] = []

    with pdfplumber.open(str(path)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            parts.append(f"## Page {idx}\n")
            if len(text.strip()) < SCANNED_PAGE_THRESHOLD:
                scanned_pages.append(idx)
                parts.append("_(little or no extractable text — see OCR/image below)_")
                parts.append("")
            else:
                parts.append(text.strip())
                parts.append("")

        if scanned_pages:
            ocr_text, ocr_images = _handle_scanned(pdf, scanned_pages, image_dir)
            if ocr_text:
                parts.append("## OCR Output")
                parts.append(ocr_text)
            saved.extend(ocr_images)

    return "\n".join(parts), saved


def _handle_scanned(pdf, page_numbers: List[int], image_dir: Path):
    has_tesseract = shutil.which("tesseract") is not None

    if has_tesseract:
        return _ocr_pages(pdf, page_numbers), []

    return "", _export_pages_as_images(pdf, page_numbers, image_dir)


def _ocr_pages(pdf, page_numbers: List[int]) -> str:
    import pytesseract

    chunks: List[str] = []
    for n in page_numbers:
        page = pdf.pages[n - 1]
        img = page.to_image(resolution=200).original
        text = pytesseract.image_to_string(img).strip()
        chunks.append(f"### Page {n}\n{text}")
    return "\n\n".join(chunks)


def _export_pages_as_images(pdf, page_numbers: List[int], image_dir: Path) -> List[Path]:
    saved: List[Path] = []
    for n in page_numbers:
        page = pdf.pages[n - 1]
        img = page.to_image(resolution=200)
        out = image_dir / f"page{n}.png"
        img.save(str(out), format="PNG")
        saved.append(out)
    return saved
