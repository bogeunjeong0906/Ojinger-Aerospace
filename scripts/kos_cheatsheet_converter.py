#!/usr/bin/env python3
"""
KOS_DOC Cheatsheet Converter
Spec: docs/plans/kos_cheatsheet_converter_spec.md
Sample: docs/domain_knowledge/KOS_cheatsheet/cooked_sample.html
"""

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup, Comment, Tag

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATE_FILENAME = ".cheatsheet_state.json"
STATE_VERSION = 1
KOS_VERSION = "kOS 1.4.0.0 documentation"

# HTML boilerplate selectors to strip before processing
STRIP_SELECTORS = [
    "nav",
    "footer",
    "head",
    "script",
    "style",
    ".wy-nav-side",
    ".wy-breadcrumbs",
    ".rst-footer-buttons",
    ".wy-nav-top",
    "#rtd-search-form",
    ".versionmodified",          # version-changed banners (keep text in-place via parent)
    ".headerlink",               # ¶ permalink anchors
]

# Admonition title → keep parent block
ADMONITION_WARNING_SELECTORS = "div.admonition.warning, div.admonition.caution, div.admonition.danger"
ADMONITION_NOTE_SELECTORS    = "div.admonition.note, div.admonition.tip, div.admonition.hint, div.admonition.seealso"

# Tuning section keywords (case-insensitive match on heading text)
TUNING_KEYWORDS = re.compile(
    r"tun|setting|parameter|configur|adjust|pid|kp|ki|kd", re.IGNORECASE
)

# Suffix/keyword pattern: WORD or WORD:WORD (all-caps KOS identifiers)
# Must have a colon (suffix chain) OR be long enough to be non-trivial (>= 8 chars)
KOS_IDENT_RE = re.compile(r"^[A-Z][A-Z0-9_]+(:[A-Z][A-Z0-9_]+)*$")
KOS_IDENT_MIN_BARE_LEN = 8  # minimum length for identifiers without a colon

# Minimum suffix inventory count before issuing a WARNING
SUFFIX_WARN_THRESHOLD = 5

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

log = logging.getLogger("kos_converter")


def _setup_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
    log.addHandler(handler)
    log.setLevel(getattr(logging, level.upper(), logging.INFO))


# ---------------------------------------------------------------------------
# HTML Parsing helpers
# ---------------------------------------------------------------------------

def _load_soup(path: Path) -> BeautifulSoup:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(text, "html.parser")


def _strip_boilerplate(soup: BeautifulSoup) -> None:
    """Remove navigation, scripts, styles, and permalink anchors in-place."""
    for sel in STRIP_SELECTORS:
        for tag in soup.select(sel):
            tag.decompose()
    # Remove HTML comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()


def _get_title(soup: BeautifulSoup) -> str:
    title_tag = soup.find("title")
    if title_tag:
        raw = title_tag.get_text(strip=True)
        # "Cooked Control — kOS 1.4.0.0 documentation" → "Cooked Control"
        return raw.split("—")[0].strip()
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else "Unknown"


def _extract_core_intent(article: Tag) -> str:
    """First meaningful paragraph after h1 and the first dl.object dd desc."""
    parts = []

    h1 = article.find("h1")
    if h1:
        # First <p> sibling after h1
        nxt = h1.find_next_sibling()
        while nxt:
            if nxt.name == "p":
                text = nxt.get_text(" ", strip=True)
                if text:
                    parts.append(text)
                    break
            if nxt.name in ("h2", "h3", "section"):
                break
            nxt = nxt.find_next_sibling()

    # First dl.object dd > p (formal definition)
    for dl in article.select("dl.object dd > p"):
        text = dl.get_text(" ", strip=True)
        if text and text not in parts:
            parts.append(text)
            break  # only first definition

    return " ".join(parts)


def _extract_warnings(article: Tag) -> list[Tag]:
    return article.select(ADMONITION_WARNING_SELECTORS)


def _extract_notes(article: Tag) -> list[Tag]:
    return article.select(ADMONITION_NOTE_SELECTORS)


def _extract_code_blocks(article: Tag) -> list[Tag]:
    """All .highlight pre blocks and bare pre>code blocks."""
    blocks: list[Tag] = []
    seen_text: set[str] = set()

    for pre in article.select("div.highlight pre, pre"):
        code_text = pre.get_text(strip=True)
        if not code_text or code_text in seen_text:
            continue
        # Skip blank or trivially short code (e.g. single-word inline)
        if len(code_text) < 4:
            continue
        seen_text.add(code_text)
        blocks.append(pre)

    return blocks


def _extract_tuning_sections(article: Tag) -> list[Tag]:
    """h2/h3 sections whose heading text matches TUNING_KEYWORDS."""
    sections = []
    for heading in article.select("h2, h3"):
        if TUNING_KEYWORDS.search(heading.get_text(strip=True)):
            # Collect siblings until next same-level heading
            section_parts: list[Tag] = [heading]
            nxt = heading.find_next_sibling()
            while nxt:
                if nxt.name == heading.name:
                    break
                if isinstance(nxt, Tag):
                    section_parts.append(nxt)
                nxt = nxt.find_next_sibling()
            if len(section_parts) > 1:  # has content beyond heading
                sections.extend(section_parts)
                sections.append(_make_tag("hr"))
    if sections and isinstance(sections[-1], Tag) and sections[-1].name == "hr":
        sections.pop()
    return sections


def _extract_suffixes(article: Tag) -> list[str]:
    """Collect unique kOS suffix/attribute identifiers from the article."""
    seen: set[str] = set()

    def _add(text: str) -> None:
        t = text.strip()
        if not t or not KOS_IDENT_RE.match(t):
            return
        # Keep if it contains a colon (suffix chain) OR is long enough to be meaningful
        if ":" in t or len(t) >= KOS_IDENT_MIN_BARE_LEN:
            seen.add(t)

    # Formal sig definitions: dl.object dt.sig .sig-name .pre
    for elem in article.select("dl.object dt.sig .sig-name .pre"):
        for token in elem.get_text(strip=True).split():
            _add(token)

    # Cross-references (e.g. STEERINGMANAGER:PITCHPID:KD) - normalise to upper
    for elem in article.select("code.xref"):
        raw = elem.get_text(strip=True).strip()
        # Normalise mixed-case (e.g. "Config:SUPPRESSAUTOPILOT" → "CONFIG:SUPPRESSAUTOPILOT")
        _add(raw.upper())

    # Inline literal code: pick those matching KOS_IDENT_RE
    for elem in article.select("code.docutils.literal .pre, span.pre"):
        for token in elem.get_text(strip=True).split():
            _add(token)

    # ── KEY FIX: scan all highlighted code blocks for colon-chain suffixes ──
    # These are the primary source of suffix definitions in most kOS docs
    # Pattern: WORD:WORD or WORD:WORD:WORD (e.g. STEERINGMANAGER:PITCHPID:KP)
    CODE_SUFFIX_RE = re.compile(r"\b([A-Z][A-Z0-9_]+(?::[A-Z][A-Z0-9_]+){1,})\b")
    for pre in article.select("div.highlight pre, pre"):
        for m in CODE_SUFFIX_RE.finditer(pre.get_text()):
            seen.add(m.group(1))

    return sorted(seen)


# ---------------------------------------------------------------------------
# HTML Rendering helpers
# ---------------------------------------------------------------------------

def _make_tag(name: str, **attrs) -> Tag:
    """Create a minimal Tag (no soup context needed)."""
    soup = BeautifulSoup(f"<{name}></{name}>", "html.parser")
    tag = soup.find(name)
    for k, v in attrs.items():
        tag[k] = v
    return tag


def _admonition_to_html(block: Tag) -> str:
    """Convert a BeautifulSoup admonition block to clean HTML snippet."""
    # Strip permalink anchors inside
    for a in block.select(".headerlink"):
        a.decompose()
    title = block.find(class_="admonition-title")
    title_text = title.get_text(strip=True) if title else "Note"
    if title:
        title.decompose()
    body = block.get_text(" ", strip=True)
    label = "⚠" if "warning" in block.get("class", []) else "ℹ"
    return (
        f'<div class="admonition">'
        f'<strong>{label} {title_text}</strong>: {body}'
        f'</div>\n'
    )


def _code_block_to_html(pre: Tag) -> str:
    code_text = pre.get_text()
    # Detect language hint from parent div class (e.g. highlight-kerboscript)
    parent = pre.parent
    lang = ""
    if parent and isinstance(parent, Tag):
        for cls in parent.get("class", []):
            if cls.startswith("highlight-") and cls != "highlight-none":
                lang = cls[len("highlight-"):]
                break
    lang_attr = f' data-lang="{lang}"' if lang else ""
    return f'<pre><code{lang_attr}>{code_text}</code></pre>\n'


def _render_cheatsheet(
    src_rel: str,
    title: str,
    core_intent: str,
    warnings: list[Tag],
    notes: list[Tag],
    code_blocks: list[Tag],
    tuning_sections: list[Tag],
    suffixes: list[str],
) -> str:
    lines: list[str] = []

    # Meta header
    lines.append(f"""<!--
CHEATSHEET_META
source_file: docs/domain_knowledge/KOS_DOC/{src_rel}
source_doc_title: {title}
source_doc_version: {KOS_VERSION}
cheatsheet_type: snippet-first, agent-oriented
-->
""")

    lines.append(f"<h1>{title}</h1>\n")

    # 1) Core Intent
    if core_intent:
        lines.append("<h2>1) Core Intent</h2>\n")
        lines.append(f"<p>{core_intent}</p>\n")

    # 2) Safety Critical Notes
    if warnings:
        lines.append("<h2>2) Safety Critical Notes</h2>\n")
        for w in warnings:
            lines.append(_admonition_to_html(w))

    # 3) Snippet Pack
    if code_blocks:
        lines.append("<h2>3) Snippet Pack</h2>\n")
        for pre in code_blocks:
            lines.append(_code_block_to_html(pre))

    # 4) Tuning / Parameters
    if tuning_sections:
        lines.append("<h2>4) Tuning / Parameters</h2>\n")
        for elem in tuning_sections:
            if isinstance(elem, Tag):
                if elem.name == "hr":
                    lines.append("<hr/>\n")
                elif elem.name in ("h2", "h3"):
                    lines.append(f"<{elem.name}>{elem.get_text(strip=True)}</{elem.name}>\n")
                elif elem.name in ("pre",):
                    lines.append(_code_block_to_html(elem))
                elif elem.name == "ul":
                    items = [li.get_text(" ", strip=True) for li in elem.select("li")]
                    if items:
                        lis = "".join(f"  <li>{i}</li>\n" for i in items)
                        lines.append(f"<ul>\n{lis}</ul>\n")
                else:
                    # For <p>, keep only the first sentence to avoid verbose prose
                    raw = elem.get_text(" ", strip=True)
                    # Skip paragraphs that look like code-dump (contain SET or LOCK)
                    first_sentence = raw.split(". ")[0].rstrip(".")
                    if first_sentence and len(first_sentence) <= 300:
                        lines.append(f"<p>{first_sentence}.</p>\n")
                    elif first_sentence:
                        lines.append(f"<p>{first_sentence[:300]}...</p>\n")

    # 5) Suffix and Key Inventory
    if suffixes:
        lines.append("<h2>5) Suffix and Key Inventory</h2>\n")
        lines.append("<ul>\n")
        for s in suffixes:
            lines.append(f"  <li>{s}</li>\n")
        lines.append("</ul>\n")

    # 6) Agent Usage Hints
    if notes:
        lines.append("<h2>6) Agent Usage Hints</h2>\n")
        for n in notes:
            lines.append(_admonition_to_html(n))

    return "".join(lines)


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def _load_state(dst_root: Path) -> dict:
    state_path = dst_root / STATE_FILENAME
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": STATE_VERSION, "last_run": None, "files": {}}


def _save_state(dst_root: Path, state: dict) -> None:
    state["last_run"] = datetime.now().isoformat(timespec="seconds")
    state_path = dst_root / STATE_FILENAME
    state_path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Per-file conversion
# ---------------------------------------------------------------------------

def _convert_file(
    src_path: Path,
    dst_path: Path,
    src_rel: str,
    dry_run: bool,
    force: bool,
    stats: dict,
    state: dict,
) -> bool:
    """
    Convert one HTML file. Returns True on success, False on error.
    Mutates stats and state in-place.
    """
    try:
        soup = _load_soup(src_path)
        _strip_boilerplate(soup)

        title = _get_title(soup)

        # Find article body; fall back to full soup
        article = (
            soup.select_one('div[itemprop="articleBody"]')
            or soup.select_one('div[role="main"]')
            or soup.body
            or soup
        )

        core_intent    = _extract_core_intent(article)
        warnings       = _extract_warnings(article)
        notes          = _extract_notes(article)
        code_blocks    = _extract_code_blocks(article)
        tuning_secs    = _extract_tuning_sections(article)
        suffixes       = _extract_suffixes(article)

        # Warnings for low-quality output
        if not code_blocks:
            log.warning("No code blocks found: %s", src_rel)
        if len(suffixes) < SUFFIX_WARN_THRESHOLD:
            log.debug("Low suffix count (%d) in: %s", len(suffixes), src_rel)

        html_out = _render_cheatsheet(
            src_rel, title,
            core_intent, warnings, notes, code_blocks, tuning_secs, suffixes,
        )

        # Validate: path preservation
        expected_rel = src_rel  # same relative path
        actual_rel   = str(dst_path.relative_to(dst_path.parents[len(dst_path.parts) - len(src_path.parts) - 1]))
        if dst_path.suffix.lower() != ".html":
            log.error("SUFFIX LOST for: %s", src_rel)
            stats["errors"] += 1
            return False

        if not dry_run:
            # Skip if exists and not forced
            if dst_path.exists() and not force:
                log.warning("EXISTS (skip): %s", src_rel)
                stats["skipped"] += 1
                return True

            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path.write_text(html_out, encoding="utf-8")

            # Update state
            state["files"][src_rel] = {
                "src_mtime": src_path.stat().st_mtime,
                "dst_mtime": dst_path.stat().st_mtime,
                "snippets":  len(code_blocks),
                "suffixes":  len(suffixes),
            }

        stats["converted"] += 1
        stats["total_snippets"]  += len(code_blocks)
        stats["total_suffixes"]  += len(suffixes)
        log.debug("OK  %s  (snippets=%d suffixes=%d)", src_rel, len(code_blocks), len(suffixes))
        return True

    except Exception as exc:
        log.error("FAILED %s: %s", src_rel, exc)
        stats["errors"] += 1
        return False


# ---------------------------------------------------------------------------
# Main conversion loop
# ---------------------------------------------------------------------------

def run(
    src_root: Path,
    dst_root: Path,
    mode: str,
    force: bool,
    report: bool,
) -> int:
    t_start = time.monotonic()

    state = _load_state(dst_root) if mode in ("incremental", "full") else {}
    dry_run = (mode == "dry-run")

    # Gather target files
    all_html = sorted(p for p in src_root.rglob("*.html") if p.is_file())
    log.info("Scanned %d HTML files under %s", len(all_html), src_root)

    # Incremental: filter to changed files only
    if mode == "incremental":
        prev = state.get("files", {})
        def _changed(p: Path) -> bool:
            rel = str(p.relative_to(src_root))
            entry = prev.get(rel)
            if not entry:
                return True
            return p.stat().st_mtime > entry.get("src_mtime", 0)
        target_files = [p for p in all_html if _changed(p)]
        log.info("Incremental: %d files need conversion", len(target_files))
    else:
        target_files = all_html

    stats = {
        "scanned":        len(all_html),
        "converted":      0,
        "skipped":        0,
        "errors":         0,
        "total_snippets": 0,
        "total_suffixes": 0,
    }

    for src_path in target_files:
        src_rel = str(src_path.relative_to(src_root))
        dst_path = dst_root / src_rel
        _convert_file(src_path, dst_path, src_rel, dry_run, force, stats, state)

    # Save state (skip for dry-run)
    if not dry_run and mode != "dry-run":
        dst_root.mkdir(parents=True, exist_ok=True)
        _save_state(dst_root, state)
        log.info("State saved: %s", dst_root / STATE_FILENAME)

    duration = time.monotonic() - t_start

    # Token estimate: chars / 4
    total_chars = sum(
        (dst_root / rel).stat().st_size
        for rel in state.get("files", {})
        if (dst_root / rel).exists()
    ) if not dry_run else 0
    token_est = total_chars // 4

    if report or True:  # always show report
        pad = "=" * 38
        print(f"\n{pad}")
        print("KOS Cheatsheet Converter Report")
        print(pad)
        print(f"Mode         : {mode}")
        print(f"Source       : {src_root}")
        print(f"Destination  : {dst_root}")
        print("-" * 38)
        print(f"Total scanned     : {stats['scanned']:>6} files")
        print(f"Converted (new)   : {stats['converted']:>6} files")
        print(f"Skipped (exist)   : {stats['skipped']:>6} files")
        print(f"Errors            : {stats['errors']:>6} files")
        print("-" * 38)
        print(f"Total snippets    : {stats['total_snippets']:>6}")
        print(f"Total suffixes    : {stats['total_suffixes']:>6}")
        if token_est:
            print(f"Estimated tokens  : ~{token_est:,}")
        print("-" * 38)
        print(f"Duration : {duration:.1f} sec")
        if not dry_run:
            print(f"State saved: {dst_root / STATE_FILENAME}")
        print(pad + "\n")

    return 0 if stats["errors"] == 0 else 1


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert KOS_DOC HTML files to agent-friendly cheatsheets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/kos_cheatsheet_converter.py --mode dry-run
  python scripts/kos_cheatsheet_converter.py --mode full --report
  python scripts/kos_cheatsheet_converter.py --mode incremental
""",
    )
    parser.add_argument(
        "--src", "-s",
        default="docs/domain_knowledge/KOS_DOC",
        help="Input root directory (default: docs/domain_knowledge/KOS_DOC)",
    )
    parser.add_argument(
        "--dst", "-d",
        default="docs/domain_knowledge/KOS_cheatsheet",
        help="Output root directory (default: docs/domain_knowledge/KOS_cheatsheet)",
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["full", "incremental", "dry-run"],
        default="full",
        help="Conversion mode (default: full)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing output files",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        default=True,
        help="Print conversion report (default: True)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    _setup_logging(args.log_level)

    src_root = Path(args.src)
    dst_root = Path(args.dst)

    if not src_root.exists():
        log.error("Source directory does not exist: %s", src_root)
        return 2

    log.info("Mode: %s | src: %s | dst: %s", args.mode, src_root, dst_root)
    return run(src_root, dst_root, args.mode, args.force, args.report)


if __name__ == "__main__":
    sys.exit(main())
