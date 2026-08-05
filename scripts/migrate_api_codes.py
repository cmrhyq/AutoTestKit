"""One-shot migration script: replace scattered *_CODE constants with core.constants.ApiCode.

Usage: python scripts/migrate_api_codes.py

Idempotent: safe to run multiple times.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files that only contain the target constants (rewrite scope).
EC_TARGET_DIRS = [
    ROOT / "tests" / "api" / "elastic_compute" / "openapi",
    ROOT / "tests" / "api" / "elastic_compute" / "extensions",
]
PORTAL_FILE = ROOT / "tests" / "api" / "portal" / "test_portal_openapi.py"

# Mapping from local constant name -> ApiCode member expression.
NAME_MAP = {
    "BUSINESS_SUCCESS_CODE": "ApiCode.SUCCESS",
    "RESOURCE_NOT_FOUND_CODE": "ApiCode.NOT_FOUND",
    "WORKLOAD_NOT_FOUND_CODE": "ApiCode.NOT_FOUND",
    "RBAC_NOT_FOUND_CODE": "ApiCode.NOT_FOUND",
    "RESOURCE_CONFLICT_CODE": "ApiCode.CONFLICT",
    "RESOURCE_ALREADY_EXISTS_CODE": "ApiCode.CONFLICT",
}

# Local declaration lines to drop entirely (whole-line match, may follow a section comment).
DECLARATION_LINE_RE = re.compile(
    r"^\s*(BUSINESS_SUCCESS_CODE|RESOURCE_NOT_FOUND_CODE|WORKLOAD_NOT_FOUND_CODE|RBAC_NOT_FOUND_CODE|RESOURCE_CONFLICT_CODE|RESOURCE_ALREADY_EXISTS_CODE)\s*=\s*\d+\s*(?:#.*)?$"
)

# Optional leading section comment that groups those declarations. Drop when the next
# non-blank line was a declaration (we handle it below inline, so this is a safe pre-strip).
SECTION_COMMENT_RE = re.compile(r"^\s*#\s*业务码.*常量.*$")

IMPORT_LINE = "from core.constants.api_codes import ApiCode"


def rewrite_test_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = original

    # 1) Drop local declaration lines (BUSINESS_SUCCESS_CODE = 2000, etc.).
    new_lines: list[str] = []
    for line in text.splitlines():
        if DECLARATION_LINE_RE.match(line):
            continue
        if SECTION_COMMENT_RE.match(line):
            continue
        new_lines.append(line)
    text = "\n".join(new_lines)
    if original.endswith("\n") and not text.endswith("\n"):
        text += "\n"

    # 2) Replace name occurrences with ApiCode member.
    for name, replacement in NAME_MAP.items():
        text = re.sub(rf"\b{name}\b", replacement, text)

    # 3) Collapse >=2 blank lines that emerged from the deletion.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 4) Insert the ApiCode import if missing and ApiCode is used.
    if "ApiCode." in text and IMPORT_LINE not in text:
        text = _insert_import(text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def _insert_import(text: str) -> str:
    """Insert the ApiCode import after the last top-level `from base.` import, or before
    the first `from core.` import, or after the module docstring / first import block."""
    lines = text.splitlines()
    insert_idx: int | None = None

    # Prefer to place immediately before the first `from core.reporting` or `from core.` import.
    for i, line in enumerate(lines):
        if re.match(r"^from core\.", line):
            insert_idx = i
            break

    if insert_idx is None:
        # Fall back: after the last top-level "import ..." / "from ... import ..." near the top.
        last_import_idx = -1
        for i, line in enumerate(lines):
            if re.match(r"^(import\s|from\s)", line):
                last_import_idx = i
            elif last_import_idx != -1 and line.strip() and not line.startswith(("import ", "from ")):
                break
        if last_import_idx == -1:
            # No imports? Insert at top after docstring.
            insert_idx = 0
        else:
            insert_idx = last_import_idx + 1

    lines.insert(insert_idx, IMPORT_LINE)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def rewrite_portal_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = original

    # Replace bare `response_json["code"] == 2000, "响应Code应等于2000"` and any residual `== 2000` on code checks.
    text = re.sub(
        r'(response_json\[\s*["\']code["\']\s*\])\s*==\s*2000',
        r"\1 == ApiCode.SUCCESS",
        text,
    )
    # Adjust the accompanying human message to reference the enum.
    text = text.replace('"响应Code应等于2000"', '"响应Code应等于 ApiCode.SUCCESS"')

    if "ApiCode." in text and IMPORT_LINE not in text:
        text = _insert_import(text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    touched: list[Path] = []
    for d in EC_TARGET_DIRS:
        for p in sorted(d.glob("test_*.py")):
            if rewrite_test_file(p):
                touched.append(p)
    if PORTAL_FILE.exists() and rewrite_portal_file(PORTAL_FILE):
        touched.append(PORTAL_FILE)

    print(f"Touched {len(touched)} files:")
    for p in touched:
        print(f"  {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
