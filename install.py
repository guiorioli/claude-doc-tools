from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent
CONVERT_SCRIPT = REPO_DIR / "convert.py"
REQUIREMENTS = REPO_DIR / "requirements.txt"

CLAUDE_DIR = Path("~/.claude").expanduser()
CLAUDE_MD = CLAUDE_DIR / "CLAUDE.md"
SETTINGS = CLAUDE_DIR / "settings.json"

START_TAG = "<!-- doc-tools:start -->"
END_TAG = "<!-- doc-tools:end -->"


def snippet() -> str:
    return (
        f"{START_TAG}\n"
        "## Reading Documents\n"
        "When asked to read .docx, .pdf, .xlsx, .xls, .pptx, .odt, .ods, .odp, .html, .rtf files:\n"
        f"1. Run: python \"{CONVERT_SCRIPT}\" <file>\n"
        "2. The script outputs markdown to stdout and writes images to temp dir with their paths\n"
        "3. Read the markdown output; if image paths are listed, read those files too\n"
        "\n"
        "Limitations and fallbacks:\n"
        "- .doc (legacy Word): not supported — ask the user to convert to .docx first\n"
        "- Scanned PDFs without Tesseract on PATH: pages are exported as images instead of text — read the images directly\n"
        "- Password-protected PDFs: script will fail — inform the user and ask them to unlock the file\n"
        "- If the script fails for any reason: inform the user of the error and, if the file is small enough, attempt to read it directly as a fallback\n"
        f"{END_TAG}\n"
    )


def allowlist_entry() -> str:
    return f"Bash(python \"{CONVERT_SCRIPT}\":*)"


def install() -> int:
    print(f"Installing dependencies from {REQUIREMENTS} ...")
    rc = subprocess.call([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    if rc != 0:
        print("pip install failed.", file=sys.stderr)
        return rc

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    _write_claude_md(install=True)
    _write_settings(install=True)
    print("doc-tools installed.")
    return 0


def uninstall() -> int:
    _write_claude_md(install=False)
    _write_settings(install=False)
    print("doc-tools uninstalled.")
    return 0


def _write_claude_md(install: bool) -> None:
    existing = CLAUDE_MD.read_text(encoding="utf-8") if CLAUDE_MD.exists() else ""
    pattern = re.compile(
        re.escape(START_TAG) + r".*?" + re.escape(END_TAG) + r"\n?",
        re.DOTALL,
    )

    if install:
        if pattern.search(existing):
            answer = input(f"{CLAUDE_MD} already contains a doc-tools block. Overwrite? [y/N]: ").strip().lower()
            if answer != "y":
                print("Skipped CLAUDE.md update.")
                return
            new_content = pattern.sub(lambda _: snippet(), existing)
        else:
            sep = "" if existing.endswith("\n") or not existing else "\n"
            new_content = existing + sep + ("\n" if existing else "") + snippet()
        CLAUDE_MD.write_text(new_content, encoding="utf-8")
        print(f"Updated {CLAUDE_MD}")
    else:
        if not pattern.search(existing):
            print("No doc-tools block found in CLAUDE.md.")
            return
        new_content = pattern.sub("", existing)
        CLAUDE_MD.write_text(new_content, encoding="utf-8")
        print(f"Removed doc-tools block from {CLAUDE_MD}")


def _write_settings(install: bool) -> None:
    data: dict = {}
    if SETTINGS.exists():
        try:
            data = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Warning: {SETTINGS} is not valid JSON; leaving it untouched.", file=sys.stderr)
            return

    allowed = data.setdefault("allowedTools", [])
    entry = allowlist_entry()

    if install:
        if entry not in allowed:
            allowed.append(entry)
            SETTINGS.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Added allowlist entry to {SETTINGS}")
        else:
            print("Allowlist entry already present.")
    else:
        if entry in allowed:
            allowed.remove(entry)
            SETTINGS.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Removed allowlist entry from {SETTINGS}")
        else:
            print("No allowlist entry to remove.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or uninstall doc-tools.")
    parser.add_argument("--uninstall", action="store_true", help="Remove doc-tools integration.")
    args = parser.parse_args()
    return uninstall() if args.uninstall else install()


if __name__ == "__main__":
    sys.exit(main())
