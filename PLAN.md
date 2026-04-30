# doc-tools — Requirements Plan

## Goal

A set of Python scripts that convert documents to markdown + extracted images,
making it easy for Claude Code to read them without parsing binary formats directly.

---

## Supported Formats

| Format | Library | License | Notes |
|---|---|---|---|
| `.docx` | `mammoth` | MIT | — |
| `.doc` | — | — | Script warns user to convert to .docx first |
| `.pdf` (text) | `pdfplumber` | MIT | — |
| `.pdf` (scanned) | `pytesseract` | Apache 2.0 | Requires Tesseract installed |
| `.xlsx` | `pandas` + `openpyxl` | BSD/MIT | — |
| `.xls` | `pandas` + `xlrd` | BSD | — |
| `.pptx` | `python-pptx` | MIT | Extracts text per slide + speaker notes |
| `.odt` / `.ods` / `.odp` | `odfpy` | Apache 2.0 | — |
| `.html` / `.htm` | `beautifulsoup4` | MIT | — |
| `.rtf` | `striprtf` | MIT | — |

---

## Output Behavior

- **Text**: printed to stdout as markdown — no files created
- **Images**: written to system temp dir (`tempfile.mkdtemp()`), paths reported in stdout for Claude to read; OS handles cleanup naturally
- **PDFs**: script auto-detects if scanned (little extractable text → tries OCR; if Tesseract is not installed → warns and extracts pages as images for Claude to read directly)

---

## Project Structure

```
doc-tools/
  convert.py          # main script, entry point
  converters/
    pdf.py
    office.py         # docx, xlsx, xls, pptx
    odf.py            # odt, ods, odp
    web.py            # html, rtf
  install.py          # cross-platform install/uninstall
  requirements.txt
  README.md
  PLAN.md             # this file
```

---

## Installation (`python install.py`)

1. Resolves the absolute path of the repository itself
2. Installs dependencies via `pip install -r requirements.txt`
3. Appends a delimited snippet to `~/.claude/CLAUDE.md`:
   ```
   <!-- doc-tools:start -->
   ...
   <!-- doc-tools:end -->
   ```
4. Adds `convert.py` to the Claude Code allowlist in `~/.claude/settings.json`

**Idempotent**: if the delimiter tags are already present, asks whether to overwrite.

`python install.py --uninstall` removes the snippet from CLAUDE.md and the entry from the allowlist.

---

## CLAUDE.md Snippet (inserted by install)

```markdown
## Reading Documents
When asked to read .docx, .pdf, .xlsx, .xls, .pptx, .odt, .ods, .odp, .html, .rtf files:
1. Run: python /absolute/path/to/doc-tools/convert.py <file>
2. The script outputs markdown to stdout and writes images to temp dir with their paths
3. Read the markdown output; if image paths are listed, read those files too
4. For .doc files: ask the user to convert to .docx first
```

---

## External Prerequisites (manual install, documented in README)

| Prerequisite | Required | Purpose |
|---|---|---|
| Python 3.9+ | Yes | Run the scripts |
| Tesseract OCR | No | Scanned PDF support |

---

## Out of Scope

- Writing / generating documents
- Password-protected PDFs
- ZIP archives containing documents
- Native `.doc` support (proprietary binary format, no pip-only solution)
- OCR via `easyocr` (too heavy; Tesseract preferred)
