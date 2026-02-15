// boot.ks
// Simple boot helper placed on boot path. Defines small helper functions
// and prints available callable functions for easy use from terminal.
// Usage: RUN 0:/boot.ks  then CALL scan_part().
// - RUN / function definition / PRINT
//   reference_docs/KOS_DOC/commands/runprogram.html: (RUN usage)
// - Core / kOSProcessor boot-related fields available at runtime
//   reference_docs/KOS_DOC/structures/vessels/kosprocessor.html:171

CORE:PART:GETMODULE("kOSProcessor"):DOEVENT("Open Terminal").
PRINT "terminal opened".

PRINT "boot.ks loaded. Available functions:".
PRINT "  - scan_part()    : runs 0:/scan_parts.ks and creates 0:/<core_tag>/parts.json".

// scan_part: runs the enhanced scan script (convenience wrapper)

PRINT "scan_part(): running 0:/scan_parts.ks...".
RUN "0:/scan_parts.ks". // reference_docs/KOS_DOC/commands/runprogram.html

switch to 0.
// end of boot.ks
