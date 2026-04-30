# claude-doc-tools

CLI tool that converts documents to Markdown + extracted images so Claude Code
can read them without parsing binary formats directly.

## Running

Always run from the repo root (imports are relative to it):

```
python convert.py <file>
```

Output: Markdown on stdout. If images were extracted, their absolute temp paths
are listed under `## Extracted Images` at the end.

## Project structure

```
convert.py          # entry point — dispatches by extension
converters/
  office.py         # docx (mammoth), xlsx/xls (pandas), pptx (python-pptx)
  pdf.py            # pdfplumber for text; pytesseract or PNG fallback for scanned pages
  odf.py            # odt, ods, odp (odfpy)
  web.py            # html (beautifulsoup4), rtf (striprtf)
install.py          # install / uninstall — updates ~/.claude/CLAUDE.md and settings.json
requirements.txt
```

## Install / uninstall

```
python install.py
python install.py --uninstall
```

Install is idempotent. It writes a delimited block between
`<!-- doc-tools:start -->` and `<!-- doc-tools:end -->` in `~/.claude/CLAUDE.md`
and adds a `Bash(python <path>/convert.py:*)` entry to `allowedTools` in
`~/.claude/settings.json`.

## Key design decisions

- **stdout only for text**: no output files created for text content.
- **System temp for images**: `tempfile.mkdtemp(prefix="doc-tools-")` — OS handles cleanup.
- **Scanned PDF detection**: pages with fewer than 50 extracted characters are treated as
  scanned. If Tesseract is on PATH, OCR is used; otherwise pages are exported as PNG.
- **No PATH dependency**: install writes the absolute repo path into CLAUDE.md, so the
  script is invoked by full path and no shell PATH changes are needed.
- **`.doc` not supported**: legacy binary format with no pip-only solution. Script
  instructs the user to convert to `.docx` first.

## External prerequisites

| Prerequisite | Required | Purpose |
|---|---|---|
| Python 3.9+ | Yes | Run the scripts |
| Tesseract OCR | No | OCR for scanned PDFs — install from https://tesseract-ocr.github.io/tessdoc/Installation.html and ensure `tesseract` is on PATH |
