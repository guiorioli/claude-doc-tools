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

# Claude Code paths
CLAUDE_DIR = Path("~/.claude").expanduser()
CLAUDE_MD = CLAUDE_DIR / "CLAUDE.md"
CLAUDE_SETTINGS = CLAUDE_DIR / "settings.json"

# OpenCode paths
OPENCODE_DIR = Path("~/.config/opencode").expanduser()
OPENCODE_JSON = OPENCODE_DIR / "opencode.json"
OPENCODE_MD = OPENCODE_DIR / "opencode.md"

START_TAG = "<!-- doc-tools:start -->"
END_TAG = "<!-- doc-tools:end -->"


def snippet(script_path: str) -> str:
    return (
        f"{START_TAG}\n"
        "## Reading Documents\n"
        "When asked to read .docx, .pdf, .xlsx, .xls, .pptx, .odt, .ods, .odp, .html, .rtf files:\n"
        f'1. Run: python "{script_path}" <file>\n'
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


def claude_allowlist_entry() -> str:
    return f'Bash(python "{CONVERT_SCRIPT}":*)'


def _detect_targets(target: str | None) -> list[str]:
    if target and target != "auto":
        if target == "both":
            return ["claude", "opencode"]
        return [target]

    has_claude = CLAUDE_DIR.exists()
    has_opencode = OPENCODE_DIR.exists()

    if has_claude and not has_opencode:
        return ["claude"]
    if has_opencode and not has_claude:
        return ["opencode"]
    if not has_claude and not has_opencode:
        print("Neither Claude Code nor OpenCode config directories were found.")
        print(f"  Claude Code expected at: {CLAUDE_DIR}")
        print(f"  OpenCode expected at:    {OPENCODE_DIR}")
        print()
        return _interactive_target_choice()

    return _interactive_target_choice()


def _interactive_target_choice() -> list[str]:
    print("Where do you want to install doc-tools?")
    print("  1) Claude Code")
    print("  2) OpenCode")
    print("  3) Both")
    while True:
        choice = input("Enter choice [1/2/3]: ").strip()
        if choice == "1":
            return ["claude"]
        if choice == "2":
            return ["opencode"]
        if choice == "3":
            return ["claude", "opencode"]
        print("Invalid choice. Please enter 1, 2 or 3.")


def install(targets: list[str]) -> int:
    print(f"Installing dependencies from {REQUIREMENTS} ...")
    rc = subprocess.call([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    if rc != 0:
        print("pip install failed.", file=sys.stderr)
        return rc

    script_path = str(CONVERT_SCRIPT).replace("\\", "/")

    if "claude" in targets:
        CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
        _write_claude_md(install=True, script_path=script_path)
        _write_claude_settings(install=True)

    if "opencode" in targets:
        OPENCODE_DIR.mkdir(parents=True, exist_ok=True)
        _write_opencode_md(install=True, script_path=script_path)
        _write_opencode_settings(install=True)

    print("doc-tools installed.")
    return 0


def uninstall(targets: list[str]) -> int:
    if "claude" in targets:
        _write_claude_md(install=False, script_path="")
        _write_claude_settings(install=False)

    if "opencode" in targets:
        _write_opencode_md(install=False, script_path="")
        _write_opencode_settings(install=False)

    print("doc-tools uninstalled.")
    return 0


# ---------------------------------------------------------------------------
# Claude Code helpers
# ---------------------------------------------------------------------------


def _write_claude_md(install: bool, script_path: str) -> None:
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
            new_content = pattern.sub(lambda _: snippet(script_path), existing)
        else:
            sep = "" if existing.endswith("\n") or not existing else "\n"
            new_content = existing + sep + ("\n" if existing else "") + snippet(script_path)
        CLAUDE_MD.write_text(new_content, encoding="utf-8")
        print(f"Updated {CLAUDE_MD}")
    else:
        if not pattern.search(existing):
            print("No doc-tools block found in CLAUDE.md.")
            return
        new_content = pattern.sub("", existing)
        CLAUDE_MD.write_text(new_content, encoding="utf-8")
        print(f"Removed doc-tools block from {CLAUDE_MD}")


def _write_claude_settings(install: bool) -> None:
    data: dict = {}
    if CLAUDE_SETTINGS.exists():
        try:
            data = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Warning: {CLAUDE_SETTINGS} is not valid JSON; leaving it untouched.", file=sys.stderr)
            return

    allowed = data.setdefault("allowedTools", [])
    entry = claude_allowlist_entry()

    if install:
        if entry not in allowed:
            allowed.append(entry)
            CLAUDE_SETTINGS.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Added allowlist entry to {CLAUDE_SETTINGS}")
        else:
            print("Allowlist entry already present.")
    else:
        if entry in allowed:
            allowed.remove(entry)
            CLAUDE_SETTINGS.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Removed allowlist entry from {CLAUDE_SETTINGS}")
        else:
            print("No allowlist entry to remove.")


# ---------------------------------------------------------------------------
# OpenCode helpers
# ---------------------------------------------------------------------------


def _write_opencode_md(install: bool, script_path: str) -> None:
    existing = OPENCODE_MD.read_text(encoding="utf-8") if OPENCODE_MD.exists() else ""
    pattern = re.compile(
        re.escape(START_TAG) + r".*?" + re.escape(END_TAG) + r"\n?",
        re.DOTALL,
    )

    if install:
        if pattern.search(existing):
            answer = input(f"{OPENCODE_MD} already contains a doc-tools block. Overwrite? [y/N]: ").strip().lower()
            if answer != "y":
                print("Skipped opencode.md update.")
                return
            new_content = pattern.sub(lambda _: snippet(script_path), existing)
        else:
            sep = "" if existing.endswith("\n") or not existing else "\n"
            new_content = existing + sep + ("\n" if existing else "") + snippet(script_path)
        OPENCODE_MD.write_text(new_content, encoding="utf-8")
        print(f"Updated {OPENCODE_MD}")
    else:
        if not pattern.search(existing):
            print("No doc-tools block found in opencode.md.")
            return
        new_content = pattern.sub("", existing)
        OPENCODE_MD.write_text(new_content, encoding="utf-8")
        print(f"Removed doc-tools block from {OPENCODE_MD}")


def _write_opencode_settings(install: bool) -> None:
    data: dict = {}
    if OPENCODE_JSON.exists():
        try:
            data = json.loads(OPENCODE_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Warning: {OPENCODE_JSON} is not valid JSON; leaving it untouched.", file=sys.stderr)
            return

    # OpenCode uses permission.bash with patterns
    permission = data.setdefault("permission", {})
    bash_perm = permission.setdefault("bash", {})
    if isinstance(bash_perm, str):
        # If someone set "bash": "allow" globally, leave it alone
        print("OpenCode bash permission is a plain string; leaving it untouched.")
        return

    entry = f'python "{CONVERT_SCRIPT}" *'

    if install:
        if bash_perm.get(entry) != "allow":
            bash_perm[entry] = "allow"
            OPENCODE_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Added bash permission to {OPENCODE_JSON}")
        else:
            print("OpenCode bash permission already present.")
    else:
        if entry in bash_perm:
            del bash_perm[entry]
            if not bash_perm:
                permission.pop("bash", None)
            if not permission:
                data.pop("permission", None)
            OPENCODE_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Removed bash permission from {OPENCODE_JSON}")
        else:
            print("No OpenCode bash permission to remove.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or uninstall doc-tools.")
    parser.add_argument("--uninstall", action="store_true", help="Remove doc-tools integration.")
    parser.add_argument(
        "--target",
        choices=["claude", "opencode", "both", "auto"],
        default="auto",
        help="Target tool(s). 'auto' detects installed tools and prompts if both are found.",
    )
    args = parser.parse_args()

    targets = _detect_targets(args.target)

    if args.uninstall:
        return uninstall(targets)
    return install(targets)


if __name__ == "__main__":
    sys.exit(main())
