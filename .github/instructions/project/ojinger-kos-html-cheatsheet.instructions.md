---
name: ojinger-kos-html-cheatsheet
description: "Use when converting docs/domain_knowledge/KOS_DOC HTML files into snippet-first KOS cheatsheet HTML output for this project."
applyTo: "docs/domain_knowledge/KOS_DOC/**/*.html"
---

# KOS DOC HTML To Cheatsheet Rules

## Purpose

Convert KOS official HTML documentation into snippet-first cheatsheets that are fast for agents to search, retrieve, and use for code generation.

## Input And Output Paths

- Input root: `docs/domain_knowledge/KOS_DOC`
- Output root: `docs/domain_knowledge/KOS_cheatsheet`
- Sample reference: `docs/domain_knowledge/KOS_cheatsheet/cooked_sample.html`

## No-Loss Structure Rules

- Replicate the source directory structure in the output tree.
- Keep the destination file name identical to the source file name.
- Never change the file suffix, including `.html`.
- Preserve suffixes and key identifiers that appear in the source, such as `STEERINGMANAGER:PITCHPID:KD`.

## Content Transformation Rules

- Record source file, source title, and version metadata at the top of the generated document.
- Structure the cheatsheet in this order:
  1. `Core Intent`
  2. `Safety Critical Notes`
  3. `Snippet Pack`
  4. `Tuning/Parameters`
  5. `Suffix and Key Inventory`
  6. `Agent Usage Hints`
- Keep prose short.
- Preserve original spelling for code, commands, APIs, and property names.
- Promote important warnings and constraints, such as `WAIT` restrictions or SAS conflicts, into an explicit safety section.

## Token Reduction Rules

- Remove narrative filler and duplicated explanations.
- Compress long background passages into one to three sentences.
- Keep only high-value examples.
- Even when compressing, preserve suffix and key inventories without loss.

## Sample Expectations

- Reference sample: `docs/domain_knowledge/KOS_cheatsheet/cooked_sample.html`
- The sample demonstrates:
  - snippet-first structure
  - separated warning and constraint content
  - suffix inventory preservation
  - output-root sample placement with a `_sample.html` name