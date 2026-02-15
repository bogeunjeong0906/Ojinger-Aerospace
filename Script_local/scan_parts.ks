// scan_parts.ks (enhanced)
// Single-run parts snapshot (stage-grouped) -> JSON
// Saves to: 0:/<CORE_TAG>/parts.json (overwrites existing file)
// Usage: RUN 0:/scan_parts.ks  or via boot helper: RUN 0:/boot.ks then CALL scan_part().
// - SHIP:PARTS / Part suffixes (UID, NAME, TITLE, STAGE, MASS, RESOURCES)
//   reference_docs/KOS_DOC/commands/parts.html:113
//   reference_docs/KOS_DOC/structures/vessels/part.html:335,349,521,403,435,563
// - CORE:TAG (use CPU name-tag for output folder)
//   reference_docs/KOS_DOC/structures/vessels/core.html:247
// - VOLUME:EXISTS / CREATEDIR / DELETE (manage output folder/file)
//   reference_docs/KOS_DOC/structures/volumes_and_files/volume.html:168,284,332
// - LEXICON / LIST (build serializable data)
//   reference_docs/KOS_DOC/structures/collections/lexicon.html:1
//   reference_docs/KOS_DOC/structures/collections/list.html:1
// - WRITEJSON (serialize kOS collections to JSON)
//   reference_docs/KOS_DOC/commands/files.html:475
// - TIMESTAMP(), ROUND(), STRING:REPLACE, :TRIM for formatting
//   reference_docs/KOS_DOC/structures/misc/time.html:193
//   reference_docs/KOS_DOC/math/basic.html:395
//   reference_docs/KOS_DOC/structures/misc/string.html:621,715

PRINT "scan_parts: collecting parts for SHIP...".

SET parts TO SHIP:PARTS. // reference_docs/KOS_DOC/commands/parts.html:113
PRINT "Part count: " + parts:LENGTH + ".".

IF parts:LENGTH = 0 {
  PRINT "No parts found on this vessel.".
  HALT.
}.

// Determine safe folder name from the running CPU's name-tag (fallback to vessel name)
SET rawTag TO core:TAG:TRIM(). // reference_docs/KOS_DOC/structures/vessels/core.html:247
IF rawTag = "" { SET rawTag TO SHIP:NAME. }.
// sanitize tag for filesystem: replace spaces and slashes
SET tag TO rawTag:REPLACE(" ", "_"):REPLACE("/","_"). // reference_docs/KOS_DOC/structures/misc/string.html:621

// Ensure output directory exists on local volume 0:
IF NOT core:VOLUME:EXISTS(tag) { core:VOLUME:CREATEDIR(tag). }. // reference_docs/KOS_DOC/structures/volumes_and_files/volume.html:321

// If parts.json already exists in that folder, delete it (one-shot scan semantics)
IF core:VOLUME:EXISTS(tag + "/parts.json") {
  core:VOLUME:DELETE(tag + "/parts.json"). // reference_docs/KOS_DOC/structures/volumes_and_files/volume.html:332
  PRINT "Existing '" + tag + "/parts.json' removed (recreating).".
}.

// Build serializable data structure (lexicon/map)
SET out TO LEXICON(). // reference_docs/KOS_DOC/structures/collections/lexicon.html:1

// metadata
SET meta TO LEXICON("vessel", SHIP:NAME, "timestamp", TIMESTAMP():FULL, "core_tag", rawTag). // reference_docs/KOS_DOC/structures/misc/time.html:193
SET out["meta"] TO meta.

// stages -> each key is stage number (string) -> value is LIST of part-objects
SET stages TO LEXICON().

SET idx TO 0.
FOR p IN parts {
  // build resource list for this part
  SET resourcesList TO LIST().
  IF p:RESOURCES:LENGTH > 0 {
    FOR r IN p:RESOURCES {
      SET rlex TO LEXICON("name", r:NAME, "amount", ROUND(r:AMOUNT,3), "capacity", ROUND(r:CAPACITY,3)). // reference_docs/KOS_DOC/structures/vessels/resource.html:199
      resourcesList:ADD(rlex).
    }.
  }.

  // part info as lexicon (serializable)
  SET partInfo TO LEXICON(
    "uid", p:UID,
    "name", p:NAME,
    "title", p:TITLE,
    "stage", p:STAGE,
    "mass_kg", ROUND(p:MASS,3),
    "resources", resourcesList
  ).

  // add to corresponding stage bucket (create if missing)
  SET stageKey TO p:STAGE:TOSTRING(). // structure TOSTRING for numbers -> string
  IF NOT stages:HASKEY(stageKey) {
    stages:ADD(stageKey, LIST()).
  }.
  stages[stageKey]:ADD(partInfo).

  SET idx TO idx + 1.
}.

SET out["stages"] TO stages.
SET out["summary"] TO LEXICON("part_count", parts:LENGTH, "stage_count", stages:KEYS:LENGTH, "total_mass_kg", ROUND(SHIP:MASS,3)).

// Write JSON to 0:/<tag>/parts.json (overwrites because we deleted above)
WRITEJSON(out, "0:/" + tag + "/parts.json"). // reference_docs/KOS_DOC/commands/files.html:475

PRINT "Wrote -> 0:/" + tag + "/parts.json  (parts=" + parts:LENGTH + ").".

// Optional: print brief per-stage counts
PRINT "Stages: " + stages:KEYS:JOIN(", ") + ".".

// Done

