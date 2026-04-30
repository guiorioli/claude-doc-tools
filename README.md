# doc-tools

CLI helper that converts documents to Markdown (and extracts images to a temp
directory) so Claude Code can read them without having to parse binary formats
directly.

## Prerequisites

- Python 3.9+
- (Optional) [Tesseract OCR](https://tesseract-ocr.github.io/tessdoc/Installation.html) on
  your `PATH` for OCR of scanned PDFs. Without it, scanned pages are exported
  as PNG images instead.

## Installation

**1. Get the repository**

With Git:
```
git clone https://github.com/guiorioli/claude-doc-tools.git
cd claude-doc-tools
```

Or download the ZIP from GitHub (green "Code" button → "Download ZIP"), extract it,
and open a terminal in the extracted folder.

**2. Run the installer**

```
python install.py
```

This will:

1. Install Python dependencies from `requirements.txt`.
2. Append a delimited snippet to `~/.claude/CLAUDE.md` telling Claude how to
   call `convert.py`.
3. Add a `Bash(python <abs path>/convert.py:*)` entry to the `allowedTools`
   list in `~/.claude/settings.json`.

The install is idempotent: if the snippet is already present in `CLAUDE.md`,
the script asks before overwriting it.

## Usage

```
python convert.py <file>
```

The Markdown is printed to stdout. If the document contained images, their
absolute paths are listed under a final `## Extracted Images` section.

Example:

```
python convert.py report.docx
```

## Supported formats

| Extension | Library |
|---|---|
| `.docx` | `mammoth` |
| `.pdf` | `pdfplumber` (text), `pytesseract` (OCR), Pillow (page images fallback) |
| `.xlsx` | `pandas` + `openpyxl` |
| `.xls` | `pandas` + `xlrd` |
| `.pptx` | `python-pptx` |
| `.odt` / `.ods` / `.odp` | `odfpy` |
| `.html` / `.htm` | `beautifulsoup4` |
| `.rtf` | `striprtf` |

`.doc` (legacy binary Word) is not supported — convert it to `.docx` first.

## Updating

`git pull` is enough as long as no new formats / dependencies were added.
After dependency changes, re-run `python install.py` to refresh the
environment.

## Uninstall

```
python install.py --uninstall
```

Removes the snippet from `~/.claude/CLAUDE.md` and the allowlist entry from
`~/.claude/settings.json`. Python packages installed by the install step are
left in place — remove them with `pip uninstall` if desired.
