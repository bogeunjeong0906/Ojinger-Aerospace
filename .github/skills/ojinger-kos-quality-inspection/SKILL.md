---
name: ojinger-kos-quality-inspection
description: "Use when inspecting KOS cheatsheet quality, collecting quality_report.json metrics, performing tiered checks, and producing a pass, conditional pass, or fail verdict for docs/domain_knowledge/KOS_cheatsheet."
argument-hint: "inspection scope or verdict target"
---

# Ojinger KOS Quality Inspection

Use this skill when the task is to run the project's 3-tier cheatsheet quality inspection workflow and produce or update `docs/plans/results/quality_report.json`.

## Scope

- Plan reference: `docs/plans/kos_cheatsheet_quality_inspection.md`
- Inspection target root: `docs/domain_knowledge/KOS_cheatsheet`
- Output report: `docs/plans/results/quality_report.json`

## Operating Rules

- Follow the repository-local Python environment when available.
- Do not commit unless the user explicitly asks for commits.
- If commits are requested, recommended checkpoints are `tier1`, `tier2`, and `final-verdict`.
- Never push without explicit user approval.

## Step 0: Preconditions

Check cheatsheet count and environment readiness.

```bash
find docs/domain_knowledge/KOS_cheatsheet -name "*.html" -not -name "cooked_sample.html" | wc -l
conda activate ./.venv && python -c "from bs4 import BeautifulSoup; print('OK')"
```

If the total is less than 138, regenerate first.

```bash
conda activate ./.venv && python scripts/kos_cheatsheet_converter.py --mode full
```

## Step 1: Tier 1 Automatic Statistics

If `scripts/kos_cheatsheet_quality_checker.py` exists, run it. Otherwise, collect Tier 1 statistics with the inline fallback below.

```bash
conda activate ./.venv && python - <<'EOF'
import json, re
from pathlib import Path
from bs4 import BeautifulSoup

src = Path("docs/domain_knowledge/KOS_DOC")
dst = Path("docs/domain_knowledge/KOS_cheatsheet")
out = {"tier1": {}, "tier2": {}, "tier3": {}, "bugs": []}

files = [f for f in dst.rglob("*.html") if f.name != "cooked_sample.html"]
has_snippet, has_suffix, empty_section, low_token = [], [], [], []
sections = ["Core Intent", "Safety", "Snippet Pack", "Tuning", "Suffix", "Agent"]

for file_path in files:
    soup = BeautifulSoup(file_path.read_text(), "html.parser")
    headings = [h.get_text(strip=True) for h in soup.find_all(["h2", "h3"])]

    missing = [section for section in sections if not any(section in heading for heading in headings)]
    if missing:
        empty_section.append({"file": str(file_path.relative_to(dst)), "missing_sections": missing})

    snippet_heading = next((h for h in soup.find_all(["h2", "h3"]) if "Snippet" in h.get_text()), None)
    suffix_heading = next((h for h in soup.find_all(["h2", "h3"]) if "Suffix" in h.get_text()), None)

    snippet_ok = bool(snippet_heading and (snippet_heading.find_next("ul") or snippet_heading.find_next("pre")))
    suffix_ok = bool(suffix_heading and suffix_heading.find_next("ul"))

    if snippet_ok:
        has_snippet.append(str(file_path.relative_to(dst)))
    if suffix_ok:
        has_suffix.append(str(file_path.relative_to(dst)))

    clean = re.sub(r"<[^>]+>", " ", file_path.read_text())
    tokens = len(re.sub(r"\s+", " ", clean)) // 4
    if tokens < 50:
        low_token.append({"file": str(file_path.relative_to(dst)), "tokens": tokens})

total = len(files)
out["tier1"] = {
    "total_files": total,
    "snippet_count": len(has_snippet),
    "snippet_rate": round(len(has_snippet) / total * 100, 1),
    "suffix_count": len(has_suffix),
    "suffix_rate": round(len(has_suffix) / total * 100, 1),
    "empty_section_count": len(empty_section),
    "empty_section_files": empty_section[:20],
    "low_token_files": low_token,
}

Path("docs/plans/results").mkdir(parents=True, exist_ok=True)
Path("docs/plans/results/quality_report.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(json.dumps(out["tier1"], indent=2, ensure_ascii=False))
EOF
```

## Step 2: Tier 2 Priority 1 Manual Checks

Read source and cheatsheet pairs and record results in `quality_report.json` under `tier2.priority1`.

### `commands/flight/cooked.html`

- At least 22 suffixes
- Includes `STEERINGMANAGER:PITCHPID:KP`, `STEERINGMANAGER:PITCHPID:KI`, `STEERINGMANAGER:PITCHPID:KD`
- Includes `SHIP:VELOCITY:SURFACE`, `SHIP:VELOCITY:ORBIT`
- Snippet includes a `LOCK STEERING TO` pattern

### `commands/flight/raw.html`

- Snippet includes `SET SHIP:CONTROL:PITCH TO` or another `SHIP:CONTROL:` pattern
- Suffixes include `SHIP:CONTROL:PITCH`, `SHIP:CONTROL:YAW`, `SHIP:CONTROL:ROLL`

### `structures/vessels/vessel.html`

- At least 10 suffixes
- Includes `SHIP:VELOCITY:SURFACE`, `SHIP:ALTITUDE`, and `SHIP:MASS`

### `structures/vessels/control.html`

- Includes `SHIP:CONTROL:PITCH`, `SHIP:CONTROL:YAW`, `SHIP:CONTROL:ROLL`, `SHIP:CONTROL:MAINTHROTTLE`
- Includes at least one snippet

## Step 3: Tier 2 Priority 2 Manual Checks

Check the following files for their required keywords.

| File | Required keywords |
|------|-------------------|
| `language/variables.html` | `LOCAL`, `GLOBAL`, `DECLARE`, `SET` |
| `language/user_functions.html` | `FUNCTION`, `PARAMETER`, `RETURN` |
| `language/flow.html` | `UNTIL`, `IF`, `WHEN...THEN` |
| `math/direction.html` | `HEADING`, `LOOKDIRUP` |
| `math/vector.html` | `V(`, `VDOT`, `VCRS` |

## Step 4: Tier 2 Priority 3 Suspect File Comparison

Compare source code block counts with cheatsheet snippet counts for the suspect set.

```bash
conda activate ./.venv && python - <<'EOF'
from pathlib import Path
from bs4 import BeautifulSoup

suspects = [
    "addons/AGX.html",
    "structures/misc/terminal.html",
    "structures/misc/resource_transfer.html",
    "language/anonymous.html",
    "language/syntax.html",
]
src = Path("docs/domain_knowledge/KOS_DOC")
dst = Path("docs/domain_knowledge/KOS_cheatsheet")

for rel in suspects:
    src_soup = BeautifulSoup((src / rel).read_text(), "html.parser")
    dst_soup = BeautifulSoup((dst / rel).read_text(), "html.parser")
    src_codes = len(src_soup.select("div.highlight"))
    dst_pres = len(dst_soup.select("pre"))
    status = "OK" if src_codes == 0 or dst_pres > 0 else "BUG"
    print(f"{status}  {rel}  src_code_blocks={src_codes}  dst_snippets={dst_pres}")
EOF
```

Add any `BUG` files to the `bugs` array in `quality_report.json`.

## Step 5: Tier 3 Suffix Accuracy Sampling

```bash
conda activate ./.venv && python - <<'EOF'
import re
from pathlib import Path
from bs4 import BeautifulSoup

samples = [
    "structures/misc/steeringmanager.html",
    "structures/misc/pidloop.html",
    "structures/vessels/orbit.html",
    "math/direction.html",
    "commands/flight/cooked.html",
]
src = Path("docs/domain_knowledge/KOS_DOC")
dst = Path("docs/domain_knowledge/KOS_cheatsheet")
pattern = re.compile(r'\b([A-Z][A-Z0-9_]+(?::[A-Z][A-Z0-9_]+)+)\b')

for rel in samples:
    src_text = (src / rel).read_text() if (src / rel).exists() else ""
    dst_soup = BeautifulSoup((dst / rel).read_text(), "html.parser")

    src_suffixes = set(pattern.findall(re.sub(r"<[^>]+>", " ", src_text)))
    dst_suffixes = set(li.get_text(strip=True) for li in dst_soup.select("li"))
    dst_suffixes = {value for value in dst_suffixes if ":" in value}

    missing = src_suffixes - dst_suffixes
    extra = dst_suffixes - src_suffixes
    print(f"--- {rel}")
    print(f"  src:{len(src_suffixes)}  dst:{len(dst_suffixes)}  missing:{len(missing)}  extra:{len(extra)}")
    if missing:
        print(f"  missing sample: {list(missing)[:5]}")
EOF
```

## Step 6: Verdict

Apply the following verdict rules.

| Grade | Condition |
|-------|-----------|
| `Pass` | `snippet_rate >= 75` and all Priority 1 checks pass and `bugs == 0` |
| `Conditional Pass` | `snippet_rate` is between 65 and 75, or there is one minor Priority 1 miss |
| `Fail` | `snippet_rate < 65`, or there are multiple Priority 1 misses, or `bugs >= 3` |

If the result is `Conditional Pass` or `Fail`, inspect each bug and decide whether it is caused by converter logic or source structure.

- Converter logic issue: update `scripts/kos_cheatsheet_converter.py` and rerun with `--mode full --force`
- Source structure exception: patch the affected cheatsheet manually

## Completion Criteria

- `docs/plans/results/quality_report.json` exists
- `verdict` is `Pass` or `Conditional Pass`
- Report verdict, key metrics, bug count, and follow-up actions to the user