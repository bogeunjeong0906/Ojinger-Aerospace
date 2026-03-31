---
name: ojinger-kos-nonhtml-cheatsheet
description: "Use when manually converting the repository's non-HTML KOS_DOC files such as .md and .ks sources into project cheatsheet HTML files with fixed target outputs, validation steps, and reporting."
argument-hint: "target non-HTML cheatsheet task or file set"
---

# Ojinger KOS Non-HTML Cheatsheet

Use this skill when the task is to manually convert the repository's non-HTML KOS documentation sources into snippet-first cheatsheet HTML files.

## Scope

- Plan reference: `docs/plans/kos_nonhtml_cheatsheet_manual.md`
- Source set is fixed to the non-HTML KOS_DOC files described in that plan.
- Output is written into `docs/domain_knowledge/KOS_cheatsheet`.

## Operating Rules

- Follow the sample HTML structure from `docs/domain_knowledge/KOS_cheatsheet/cooked_sample.html`.
- Keep all generated cheatsheets snippet-first and agent-oriented.
- When the current agent policy does not permit autonomous commits, do not commit unless the user explicitly asks.
- If the user does request commits, recommended checkpoints are `p0-p1`, `p2`, and `p3-final`.
- Never push without explicit user approval.

## Step 0: Preconditions

Check the sample file and ensure the output directories exist.

```bash
ls docs/domain_knowledge/KOS_cheatsheet/cooked_sample.html
mkdir -p docs/domain_knowledge/KOS_cheatsheet/note
mkdir -p docs/domain_knowledge/KOS_cheatsheet/mod
mkdir -p docs/domain_knowledge/KOS_cheatsheet/kOS-Ferram-master
mkdir -p docs/domain_knowledge/KOS_cheatsheet/kOS.MechJeb2.Addon-main
```

## HTML Template Structure

All generated cheatsheets should follow this structure.

```html
<!--
CHEATSHEET_META
source_file: {source relative path}
source_doc_title: {document title}
source_doc_version: {version or N/A}
cheatsheet_type: snippet-first, agent-oriented
-->

<h1>{document title} - Cheat Sheet</h1>

<h2>1) Core Intent</h2>
<p>{1 to 3 sentence purpose summary}</p>

<h2>2) Safety Critical Notes</h2>
<ul>
  <li>{warning}</li>
</ul>

<h2>3) Snippet Pack (Directly Usable)</h2>
<pre><code>{usable code pattern}</code></pre>

<h2>4) Tuning / Parameters</h2>
<pre><code>{parameter notes or table}</code></pre>

<h2>5) Suffix and Key Inventory (No-loss policy)</h2>
<ul>
  <li>{IDENTIFIER:SUFFIX}</li>
</ul>

<h2>6) Agent Usage Hints</h2>
<ul>
  <li>{agent usage note}</li>
</ul>
```

## Step 1: P0 - `note/terminal_open.html`

- Read source: `docs/domain_knowledge/KOS_DOC/note/terminal_open.md`
- Write output: `docs/domain_knowledge/KOS_cheatsheet/note/terminal_open.html`
- Required content:
  - Core Intent: how to open the kOS processor terminal from a script
  - Safety Notes: module name may differ for custom processor parts
  - Snippet: preserve the README code block
  - Suffix inventory: `CORE:PART`, `CORE:PART:GETMODULE`
  - Agent hints: mention use with `TERMINAL:*` commands
- Validation:

```bash
grep -c "GETMODULE" docs/domain_knowledge/KOS_cheatsheet/note/terminal_open.html
```

## Step 2: P1 - `mod/kerbal_engineer_redux.html`

- Read source: `docs/domain_knowledge/KOS_DOC/mod/kerbal_engineer_redux.md`
- Write output: `docs/domain_knowledge/KOS_cheatsheet/mod/kerbal_engineer_redux.html`
- Required content:
  - Core Intent: expose KerbalEngineer metrics such as delta-v and TWR to kOS
  - Safety Notes: mod required, perform availability checks first
  - Snippet: convert README examples into `<pre><code>` blocks
  - Suffix inventory: collect all `ADDONS:KE:*` and relevant `SHIP:*` identifiers
  - Agent hints: recommend guarding runtime access with availability checks
- Validation:

```bash
grep -c "<li>" docs/domain_knowledge/KOS_cheatsheet/mod/kerbal_engineer_redux.html
```

## Step 3: P2 - `kOS-Ferram-master/README.html`

- Read both sources:
  - `docs/domain_knowledge/KOS_DOC/kOS-Ferram-master/README.md`
  - `docs/domain_knowledge/KOS_DOC/kOS-Ferram-master/kosferramtest.ks`
- Write output: `docs/domain_knowledge/KOS_cheatsheet/kOS-Ferram-master/README.html`
- Required content:
  - Core Intent: real-time FAR aerodynamic data and control access from kOS
  - Safety Notes: require `ADDONS:FAR:ISAVAILABLE`, note immediate flight effects
  - Snippet: keep the full loop structure from `kosferramtest.ks`, convert print-only checks into comments when appropriate
  - Required suffixes:
    - `ADDONS:FAR:ISAVAILABLE`
    - `ADDONS:FAR:IAS`
    - `ADDONS:FAR:TAS`
    - `ADDONS:FAR:MACH`
    - `ADDONS:FAR:CL`
    - `ADDONS:FAR:CD`
    - `ADDONS:FAR:CM`
    - `ADDONS:FAR:REFAREA`
    - `ADDONS:FAR:DYNPRES`
    - `ADDONS:FAR:STALLFRACTION`
  - Agent hints: note that all `ADDONS:FAR:*` items are unusable without FAR
- Validation:

```bash
grep -c "ADDONS:FAR" docs/domain_knowledge/KOS_cheatsheet/kOS-Ferram-master/README.html
```

## Step 4: P3 - `kOS.MechJeb2.Addon-main/README.html`

- Read sources in order:
  - `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/README.md`
  - `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/CoreWrapperTest.ks`
  - `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/AscentWrapperTest.ks`
  - `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/VesselWrapperTest.ks`
  - `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/InfoWrapperTest.ks`
  - `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/TestRunner.ks` as reference only
- Write output: `docs/domain_knowledge/KOS_cheatsheet/kOS.MechJeb2.Addon-main/README.html`
- Required content:
  - Core Intent: integrated MechJeb2 autopilot control from kOS
  - Safety Notes: mod required, check `ADDONS:MJ:AVAILABLE`, configure orbit parameters before ascent, avoid control conflicts
  - Snippet sections:
    - availability check
    - core access
    - ascent autopilot
    - vessel state reads
    - info item reads
  - Remove test assertions and menu UI code from extracted snippets
  - Inventory all `ADDONS:MJ:*` identifiers from the README without loss
  - Tuning section should summarize ascent parameters such as `PITCHANGLE`, `TURNSHAPE`, and `DESIREDORBITALTITUDE`
- Validation:

```bash
grep -c "ADDONS:MJ" docs/domain_knowledge/KOS_cheatsheet/kOS.MechJeb2.Addon-main/README.html
```

## Step 5: Final Validation

Confirm all four output files exist.

```bash
for f in \
  "docs/domain_knowledge/KOS_cheatsheet/note/terminal_open.html" \
  "docs/domain_knowledge/KOS_cheatsheet/mod/kerbal_engineer_redux.html" \
  "docs/domain_knowledge/KOS_cheatsheet/kOS-Ferram-master/README.html" \
  "docs/domain_knowledge/KOS_cheatsheet/kOS.MechJeb2.Addon-main/README.html"; do
  if [ -f "$f" ]; then
    echo "OK  $f"
  else
    echo "MISSING  $f"
  fi
done
```

Check that the six required sections exist in each output file.

```bash
conda activate ./.venv && python - <<'EOF'
from pathlib import Path
from bs4 import BeautifulSoup

files = [
    "docs/domain_knowledge/KOS_cheatsheet/note/terminal_open.html",
    "docs/domain_knowledge/KOS_cheatsheet/mod/kerbal_engineer_redux.html",
    "docs/domain_knowledge/KOS_cheatsheet/kOS-Ferram-master/README.html",
    "docs/domain_knowledge/KOS_cheatsheet/kOS.MechJeb2.Addon-main/README.html",
]
sections = ["Core Intent", "Safety", "Snippet", "Tuning", "Suffix", "Agent"]

for path in files:
    soup = BeautifulSoup(Path(path).read_text(), "html.parser")
    headings = [h.get_text(strip=True) for h in soup.find_all(["h2", "h3"])]
    missing = [section for section in sections if not any(section in heading for heading in headings)]
    print(path, "OK" if not missing else f"MISSING {missing}")
EOF
```

## Completion Criteria

- All four HTML files exist
- Each file has all six major sections
- P1 through P3 files include at least one `<pre><code>` block
- P2 contains at least five `ADDONS:FAR:` identifiers
- P3 contains at least ten `ADDONS:MJ:` identifiers
- Report generated files and notable snippet or suffix coverage back to the user