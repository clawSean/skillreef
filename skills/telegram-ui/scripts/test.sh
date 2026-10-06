#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "FAIL: python3 is required" >&2
  exit 1
fi
exec python3 - "$SKILL_DIR" <<'PY'
from __future__ import annotations
import json
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote
from pathlib import Path
root = Path(sys.argv[1]).resolve(); skill = root / "SKILL.md"; script = root / "scripts" / "test.sh"
passed = 0; failed = 0
def check(ok: bool, label: str) -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS: {label}")
    else:
        failed += 1
        print(f"  FAIL: {label}", file=sys.stderr)
print("=== telegram-ui validation ===")
check(skill.is_file() and skill.stat().st_size > 0, "SKILL.md exists and is non-empty")
text = skill.read_text(encoding="utf-8") if skill.is_file() else ""
front = "\n".join(text.splitlines()[:12])
check(bool(re.search(r'^name:\s*["\']?telegram-ui["\']?\s*$', front, re.M)), "frontmatter name matches directory")
check(bool(re.search(r'^description:\s*\S.+$', front, re.M)), "frontmatter has a description")
check(len(text.encode("utf-8")) <= 8_000, "SKILL.md is at most 8,000 bytes")
check(text.count("LOCAL-STATUS") == 1, "LOCAL-STATUS token appears exactly once")
for heading in (
    "## 1. Read the current surface",
    "## 2. Choose the delivery path",
    "## 3. Compose the body",
    "## 4. Choose the interaction",
    "## 5. Handle media and special branches",
    "## 6. Verify delivery and renderer claims",
    "## Reference boundary",
):
    check(text.count(heading) == 1, f"unique section: {heading}")
expected_reference_names = {
    "payload-recipes.md",
    "rich-message-client-compat.md",
    "rich-rendering-matrix.md",
    "telegram-admin-control.md",
    "telegram-forum-topics.md",
    "telegram-mini-apps.md",
}
references = sorted((root / "references").glob("*.md"))
check({path.name for path in references} == expected_reference_names, "canonical reference set is complete")
for path in references:
    rel = path.relative_to(root).as_posix()
    check(f"({rel}" in text, f"reference linked directly: {rel}")
for stale in (root / "BASELINE_TEST_AUDIT.md", root / "progress.md"):
    check(not stale.exists(), f"stale root record retired: {stale.name}")
all_markdown = [skill, *references]
for path in [*all_markdown, script]:
    check(len(path.read_text(encoding="utf-8").splitlines()) <= 220, f"reading budget: {path.relative_to(root)}")
link_errors: list[str] = []
link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
def markdown_fragments(path: Path) -> set[str]:
    fragments: set[str] = set(re.findall(r'<a\s+(?:name|id)=["\']([^"\']+)', path.read_text(encoding="utf-8"), re.I))
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            label = re.sub(r"<[^>]+>|[`*_~]", "", heading.group(1).lower())
            fragments.add(re.sub(r"\s+", "-", re.sub(r"[^\w\- ]", "", label).strip()))
    return fragments
for path in all_markdown:
    for target in link_pattern.findall(path.read_text(encoding="utf-8")):
        target = unquote(target.strip().strip("<>"))
        file_part, _, fragment = target.partition("#")
        if not file_part or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", file_part):
            continue
        resolved = Path(file_part) if Path(file_part).is_absolute() else path.parent / file_part
        if not resolved.resolve().exists():
            link_errors.append(f"{path.relative_to(root)} -> {target}")
        elif fragment and resolved.suffix.lower() == ".md" and fragment not in markdown_fragments(resolved.resolve()):
            link_errors.append(f"{path.relative_to(root)} -> missing fragment: {target}")
check(not link_errors, "all local Markdown links resolve")
for error in link_errors:
    print(f"    {error}", file=sys.stderr)
fence_errors: list[str] = []
json_blocks: list[tuple[Path, int, str]] = []
bash_blocks: list[tuple[Path, int, str]] = []
for path in all_markdown:
    lines = path.read_text(encoding="utf-8").splitlines()
    open_lang: str | None = None
    open_marker = ""
    open_line = 0
    buf: list[str] = []
    for line_no, line in enumerate(lines, 1):
        if open_lang is None:
            match = re.fullmatch(r" {0,3}(`{3,}|~{3,})([^`]*)", line)
            if match:
                open_marker = match.group(1)
                info = match.group(2).strip()
                open_lang = info.split()[0].lower() if info else "plain"
                open_line = line_no
                buf = []
            continue
        close_pattern = rf" {{0,3}}{re.escape(open_marker[0])}{{{len(open_marker)},}}\s*"
        if re.fullmatch(close_pattern, line):
            body = "\n".join(buf) + "\n"
            if open_lang == "json":
                json_blocks.append((path, open_line, body))
            elif open_lang in {"bash", "sh", "shell"}:
                bash_blocks.append((path, open_line, body))
            open_lang = None
            open_marker = ""
            open_line = 0
            buf = []
        else:
            buf.append(line)
    if open_lang is not None:
        fence_errors.append(f"{path.relative_to(root)}:{open_line}: unclosed {open_lang or 'plain'} fence")
check(not fence_errors, "all fenced code blocks are balanced")
for error in fence_errors:
    print(f"    {error}", file=sys.stderr)
json_errors: list[str] = []
decoded: list[tuple[Path, int, object]] = []
def reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")
for path, line_no, body in json_blocks:
    try:
        decoded.append((path, line_no, json.loads(body, parse_constant=reject_json_constant)))
    except json.JSONDecodeError as exc:
        json_errors.append(f"{path.relative_to(root)}:{line_no + exc.lineno}: {exc.msg}")
    except ValueError as exc:
        json_errors.append(f"{path.relative_to(root)}:{line_no}: {exc}")
check(len(json_blocks) > 0, f"JSON recipe inventory is non-zero ({len(json_blocks)})")
check(not json_errors, f"all {len(json_blocks)} JSON recipes are strict-valid")
for error in json_errors:
    print(f"    {error}", file=sys.stderr)
by_file: dict[str, int] = {}
for path, _, _ in json_blocks:
    by_file[path.name] = by_file.get(path.name, 0) + 1
check(by_file.get("payload-recipes.md", 0) >= 12, "payload-recipes.md has broad action coverage")
check(by_file.get("telegram-forum-topics.md", 0) >= 3, "forum-topic recipes are present")
legacy_fields: list[str] = []
top_level_actions: set[str] = set(); interaction_types: set[str] = set()
def walk(value: object, path: Path, line_no: int) -> None:
    if isinstance(value, dict):
        action = value.get("action")
        if isinstance(action, dict) and isinstance(action.get("type"), str):
            interaction_types.add(action["type"])
        if "label" in value:
            if not isinstance(action, dict) or not isinstance(action.get("type"), str) or not action["type"]:
                legacy_fields.append(f"{path.relative_to(root)}:{line_no}: labeled control lacks action.type")
        for nested in value.values():
            walk(nested, path, line_no)
    elif isinstance(value, list):
        for nested in value:
            walk(nested, path, line_no)
for path, line_no, value in decoded:
    if isinstance(value, dict) and isinstance(value.get("action"), str):
        top_level_actions.add(value["action"])
    walk(value, path, line_no)
check(not legacy_fields, "canonical labeled controls use typed actions")
for error in legacy_fields:
    print(f"    {error}", file=sys.stderr)
required_actions = {"send", "poll", "edit", "react", "sticker", "sticker-search", "topic-create", "topic-edit"}
required_types = {"callback", "url", "web-app", "copy-text"}
missing_actions = sorted(required_actions - top_level_actions); missing_types = sorted(required_types - interaction_types)
check(not missing_actions and not missing_types, "payload recipes cover required actions and interaction types")
if missing_actions:
    print(f"    missing actions: {', '.join(missing_actions)}", file=sys.stderr)
if missing_types:
    print(f"    missing interaction types: {', '.join(missing_types)}", file=sys.stderr)
bash_errors: list[str] = []
for path, line_no, body in bash_blocks:
    with tempfile.NamedTemporaryFile("w", suffix=".sh", encoding="utf-8") as handle:
        handle.write(body)
        handle.flush()
        result = subprocess.run(["bash", "-n", handle.name], capture_output=True, text=True)
    if result.returncode != 0:
        bash_errors.append(f"{path.relative_to(root)}:{line_no}: {result.stderr.strip()}")
check(len(bash_blocks) > 0, f"Bash example inventory is non-zero ({len(bash_blocks)})")
check(not bash_errors, f"all {len(bash_blocks)} Bash examples parse")
for error in bash_errors:
    print(f"    {error}", file=sys.stderr)
combined = "\n".join(path.read_text(encoding="utf-8") for path in all_markdown)
unsafe = re.findall(r"https?://api\.telegram\.org/bot[^\s)]*", combined, flags=re.I)
check(not unsafe, "no token-bearing Bot API endpoint patterns")
for match in unsafe:
    print(f"    found: {match}", file=sys.stderr)
def section(start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]
surface = section("## 1. Read the current surface", "## 2. Choose the delivery path"); delivery = section("## 2. Choose the delivery path", "## 3. Compose the body")
compose = section("## 3. Compose the body", "## 4. Choose the interaction"); interaction = section("## 4. Choose the interaction", "## 5. Handle media and special branches")
media = section("## 5. Handle media and special branches", "## 6. Verify delivery and renderer claims"); verify = section("## 6. Verify delivery and renderer claims", "## Reference boundary")
check(all(term in surface for term in ("response_format", "runtime authority", "selected account", "never infer", "runtime conflicts")) and all(term in text for term in ("After compaction or resume", "re-read", "substantial Telegram final")), "runtime, account, and compaction recovery stay explicit")
check(all(term in text for term in ("every visible Telegram", "first pass", "Reading", "not completion", "do not add a second model pass")), "first-pass compliance imperative replaces review-pass reliance")
check(all(term in delivery for term in ("standard final path", "suppressing", "reply-time TTS", "route-scoped", "exact path", "passes a canary", "active schema")), "delivery path preserves final/TTS safety and route-scoped breaks")
check(all(term in re.sub(r"\s+", " ", compose) for term in ("Hard default", "every authored prose paragraph or thought break", "one empty", "source-adjacent `<br><br>`", "plain `\\n\\n` is not", "Client wrapping")), "authored prose breaks require explicit visual air")
check(all(term in compose for term in ("real source", "syntax only", "native spacing", "block-level HTML islands", "native `###` heading", "not bold alone", "never", "inline scan")), "headings rely on native spacing while rich boundaries stay explicit")
compat_text = (root / "references" / "rich-message-client-compat.md").read_text(encoding="utf-8"); compat_flat = re.sub(r"\s+", " ", compat_text); matrix_text = (root / "references" / "rich-rendering-matrix.md").read_text(encoding="utf-8")
boundary_terms = ("Pick each separator by boundary", "`heading/block ↔ body`", "`prose → prose`", "`literal list → prose`", "`literal item → literal item`", "First.<br><br>Next paragraph.", "Last item.<br><br>Next paragraph.")
check(all(term in compose for term in boundary_terms), "boundary map owns heading, prose, list exit, and item separators")
check(all(term in compose for term in ("Never send prose paragraphs separated only by source blank lines", "rich", "`message` sends", "each prose break", "source-adjacent", "`<br><br>`")), "prose serialization forbids source-only blank lines")
check(all(term in compat_flat for term in ("separator boundary map", "list-density rule", "semantic markup", "exact delivery path", "separate source paragraph", "real source blank lines")), "spacing fallback routes to canonical rules")
check(all(term in compose for term in ("Use literal `•` prose/status rows", "Reserve semantic lists", "bare source newlines can collapse", "separators", "density rule", "Never use", "block boundaries")), "structured and literal list paths preserve boundary-specific spacing"); check(all(term in re.sub(r"\s+", " ", compose) for term in ("Rich by default", "as many supported features as fit", "decorative blocks", "No numeric cap", "maximize useful variety")) and "skip decorative blocks" not in compose and "two purposeful rich structures" not in compose, "rich formatting has no arbitrary cap")
check(all(term in compose for term in ("Literal lists are compact by default", "90 visible characters", "one source-adjacent `<br>`", "If any item exceeds", "`<br><br>` between every item", "rendered characters", "excluding formatting syntax", "beyond two")), "literal list density uses the deterministic long-item threshold")
check(len("• " + "x" * 88) == 90 and len("• " + "x" * 89) == 91, "90-visible-character list threshold fixture is exact")
unsafe_literal = re.compile(r"(?m)^•[^\n]*\n•"); check(bool(unsafe_literal.search("• a\n• b")) and not unsafe_literal.search("• a<br>• b") and not unsafe_literal.search("<ul><li>a</li><li>b</li></ul>") and not unsafe_literal.search(compose), "literal-bullet fixture rejects bare newline and scans the skill")
check(all(term in compose for term in ("Multiple headings are fine", "each starts", "after real `\\n\\n`", "Never emit `<br><br>###`", "end prior block first", "inline code for simple one-line values", "newline/escape-sequence", "leaked backticks")) and not re.search(r"<br><br>[ \t]*\n", text) and not re.search(r"(?m)^#{1,6}.*<br>", text), "heading boundaries and code-span safety stay explicit")
check(all(term in compose for term in ("copy-text", "1–256", "separate legacy", "whole-message", "local token", "Never fake Copy")), "Copy Text uses the approved companion fallback and preserves token safety")
check(all(term in compose for term in ("Unknown surfaces", "complete row-for-row compact mirror")), "table fallback and mirror remain mandatory")
check(all(term in interaction for term in ("reaction", "replyTo", "buttons", "poll", "edit", "pin", "plain-text menu", "Group/topic Mini", "direct-link URL", "true `web-app`", "private-chat", "presentation.blocks", "top-level `buttons` are stripped", "Mirror choices")), "interaction routing and group web-app prohibition remain explicit")
check(all(term in re.sub(r"\s+", " ", media) for term in ("Captions", "literal line breaks", "true 1:1", "centered safe area", "unless another ratio", "injected voice transcript", "If absent, say so", "never pretend", "IDs distinct")), "caption, thumbnail, transcript, and ID rules remain explicit")
check(all(term in verify for term in ("first-pass composition", "not a manual checklist", "active schema", "real message ID", "actual client", "acknowledge and repair once", "suspend the failing feature")) and "Re-read the final" not in verify, "delivery verification remains without a manual pre-send checklist")
check(not any(term in compose for term in ("single-sentence", "multi-sentence", "natural wrapping alone", "likely multi-line", "likely single-line", "more than half are compact", "50/50 list tie")) and all(term in matrix_text for term in ("### T22:", "one `InputRichBlockParagraph`", "not a reliable separator", "### T23:", "ordinary-final path")), "obsolete subjective density policy stays absent and route evidence remains")
check(not re.search(r"\b20\d{2}[.-]\d{1,2}", text + "\n" + compat_text), "dated renderer evidence stays outside operating guides")
check(not re.search(r"(?im)^#+\s*(roadmap|todo)|\bFIXME\b", combined), "no unresolved roadmap or TODO records")
print(f"\nResults: {passed} passed, {failed} failed"); raise SystemExit(1 if failed else 0)
PY
