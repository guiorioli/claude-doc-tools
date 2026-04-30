from __future__ import annotations

import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from converters.office import convert_docx, convert_xlsx, convert_xls, convert_pptx
from converters.pdf import convert_pdf
from converters.odf import convert_odt, convert_ods, convert_odp
from converters.web import convert_html, convert_rtf


HANDLERS = {
    ".docx": convert_docx,
    ".xlsx": convert_xlsx,
    ".xls": convert_xls,
    ".pptx": convert_pptx,
    ".pdf": convert_pdf,
    ".odt": convert_odt,
    ".ods": convert_ods,
    ".odp": convert_odp,
    ".html": convert_html,
    ".htm": convert_html,
    ".rtf": convert_rtf,
}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python convert.py <file>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1]).expanduser().resolve()
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    ext = path.suffix.lower()

    if ext == ".doc":
        print(
            "Error: legacy .doc format is not supported. "
            "Please convert the file to .docx (e.g. open in Word/LibreOffice and Save As .docx) and try again.",
            file=sys.stderr,
        )
        return 1

    handler = HANDLERS.get(ext)
    if handler is None:
        print(f"Error: unsupported extension '{ext}'", file=sys.stderr)
        return 1

    image_dir = Path(tempfile.mkdtemp(prefix="doc-tools-"))

    try:
        markdown, images = handler(path, image_dir)
    except Exception as exc:
        print(f"Error processing {path.name}: {exc}", file=sys.stderr)
        return 1

    sys.stdout.write(markdown.rstrip() + "\n")
    if images:
        sys.stdout.write("\n## Extracted Images\n")
        for img in images:
            sys.stdout.write(f"{img}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
