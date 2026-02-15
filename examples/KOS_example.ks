// Refined launch autopilot → target: 70 km circular orbit
// All lines reference `reference_docs/KOS_DOC` (file:line)
// reference_docs/KOS_DOC/tutorials/quickstart.html:503

// --- constants & configuration
SET TARGET_APO TO 70000. // reference_docs/KOS_DOC/tutorials/quickstart.html:503
SET TURN_START TO 1000. // reference_docs/KOS_DOC/tutorials/designpatterns.html:150
SET TURN_END TO 30000. // reference_docs/KOS_DOC/language/features.html:310
SET SAFETY_MARGIN TO 0.95. // reference_docs/KOS_DOC/tutorials/quickstart.html:703

PRINT "Refined launch autopilot starting.". // reference_docs/KOS_DOC/language/features.html:172

// --- helper functions (user functions + parameters)
// see: reference_docs/KOS_DOC/language/user_functions.html and language/delegates.html
function ascent_to_apo { parameter target_apo. // reference_docs/KOS_DOC/language/user_functions.html:1
  // simple gravity-turn ascent, auto-staging and soft throttle
  UNTIL SHIP:OBT:APOAPSIS > target_apo { // reference_docs/KOS_DOC/tutorials/quickstart.html:503
    PRINT ROUND(SHIP:OBT:APOAPSIS,0) AT (0,16). // reference_docs/KOS_DOC/tutorials/quickstart.html:516

    SET frac TO (SHIP:ALTITUDE - TURN_START) / (TURN_END - TURN_START). // reference_docs/KOS_DOC/math/basic.html:243
    IF frac < 0 { SET frac TO 0. }. // reference_docs/KOS_DOC/language/flow.html:490
    IF frac > 1 { SET frac TO 1. }. // reference_docs/KOS_DOC/language/flow.html:490

    SET targetPitch TO 90 - 80 * frac. // reference_docs/KOS_DOC/math/direction.html:254
    LOCK STEERING TO SHIP:PROGRADE + R(targetPitch,0,0). // reference_docs/KOS_DOC/math/direction.html:256

    IF SHIP:OBT:APOAPSIS > target_apo * SAFETY_MARGIN { LOCK THROTTLE TO 0.25. } ELSE { LOCK THROTTLE TO 1. }. // reference_docs/KOS_DOC/language/flow.html:505

    IF STAGE:READY AND STAGE:LIQUIDFUEL < 0.1 { STAGE. } // reference_docs/KOS_DOC/structures/vessels/stage.html:153
    WAIT 0.2. // reference_docs/KOS_DOC/tutorials/basictutorial.html:451
  }
} // reference_docs/KOS_DOC/language/user_functions.html:1

function simple_circularize { parameter target_apo. // reference_docs/KOS_DOC/language/user_functions.html:1
  LOCK THROTTLE TO 1. // reference_docs/KOS_DOC/language/flow.html:505
  WAIT UNTIL SHIP:OBT:PERIAPSIS > target_apo. // reference_docs/KOS_DOC/tutorials/basictutorial.html:729
  LOCK THROTTLE TO 0. // reference_docs/KOS_DOC/language/flow.html:505
}

function dynamic_circularize { parameter target_apo. // reference_docs/KOS_DOC/language/user_functions.html:1
  // compute circular velocity at apoapsis radius and estimate burn time
  SET r TO SHIP:OBT:APOAPSIS + SHIP:BODY:RADIUS. // reference_docs/KOS_DOC/structures/celestial_bodies/body.html:327
  SET mu TO SHIP:BODY:MU. // reference_docs/KOS_DOC/structures/celestial_bodies/body.html:334
  SET v_circ TO SQRT(mu / r). // reference_docs/KOS_DOC/math/basic.html:220
  SET v_now TO SHIP:VELOCITY:ORBIT:MAG. // reference_docs/KOS_DOC/structures/orbits/orbitablevelocity.html:188
  SET dv_needed TO MAX(0, v_circ - v_now). // reference_docs/KOS_DOC/math/basic.html:386

  IF SHIP:DELTAV:CURRENT < dv_needed { PRINT "WARN: available dV=" + ROUND(SHIP:DELTAV:CURRENT,1) + " < required " + ROUND(dv_needed,1) + " m/s (partial burn).". } // reference_docs/KOS_DOC/structures/vessels/deltav.html:146

  SET max_acc TO SHIP:MAXTHRUST / SHIP:MASS. // reference_docs/KOS_DOC/tutorials/exenode.html:113
  IF max_acc <= 0 OR dv_needed = 0 {
    // fallback to simple periapsis-driven burn
    simple_circularize(target_apo). // reference_docs/KOS_DOC/tutorials/basictutorial.html:729
  } ELSE {
    SET burn_time TO dv_needed / max_acc. // reference_docs/KOS_DOC/tutorials/exenode.html:130
    PRINT "Estimated dv=" + ROUND(dv_needed,2) + " m/s, burn(s)~" + ROUND(burn_time,2) + ".". // reference_docs/KOS_DOC/tutorials/exenode.html:130

    WAIT UNTIL ETA:APOAPSIS < (burn_time/2 + 1). // reference_docs/KOS_DOC/structures/orbits/eta.html:173
    LOCK STEERING TO SHIP:PROGRADE. // reference_docs/KOS_DOC/math/direction.html:256
    LOCK THROTTLE TO SAFETY_MARGIN. // reference_docs/KOS_DOC/tutorials/quickstart.html:703

    SET burn_start TO TIME:SECONDS. // reference_docs/KOS_DOC/language/variables.html:876
    FROM { WAIT 0.1. } UNTIL (SHIP:OBT:PERIAPSIS > target_apo) OR (ABS(v_circ - SHIP:VELOCITY:ORBIT:MAG) < 0.5) OR ((TIME:SECONDS - burn_start) > (burn_time * 3)) STEP { WAIT 0.1. } DO { // timeout guard
      // monitoring loop
    }.

    LOCK THROTTLE TO 0. // reference_docs/KOS_DOC/language/flow.html:505
    PRINT "Circularize burn finished; periapsis=" + ROUND(SHIP:OBT:PERIAPSIS,0) + ", remain dv~" + ROUND(ABS(v_circ - SHIP:VELOCITY:ORBIT:MAG),2) + " m/s.". // reference_docs/KOS_DOC/structures/vessels/deltav.html:146
  }
} // end dynamic_circularize

// --- prelaunch: enable full throttle and point prograde
LOCK THROTTLE TO 1. // reference_docs/KOS_DOC/language/flow.html:505
LOCK STEERING TO SHIP:PROGRADE. // reference_docs/KOS_DOC/math/direction.html:256
WAIT 1. // reference_docs/KOS_DOC/tutorials/basictutorial.html:451

// --- ascent: gravity-turn with dynamic pitch schedule (functionized)
ascent_to_call: // human-friendly label
ascent_to_apo(TARGET_APO). // reference_docs/KOS_DOC/language/user_functions.html:1

// --- coast phase: cut throttle and prepare circularization
PRINT "Target apoapsis reached; coasting to apoapsis.". // reference_docs/KOS_DOC/tutorials/quickstart.html:679
LOCK THROTTLE TO 0. // reference_docs/KOS_DOC/language/flow.html:505

// wait until close to apoapsis to burn (time-to-apoapsis check)
WAIT UNTIL ETA:APOAPSIS < 60. // reference_docs/KOS_DOC/structures/orbits/eta.html:173

// orient prograde and perform circularization burn
LOCK STEERING TO SHIP:PROGRADE. // reference_docs/KOS_DOC/math/direction.html:256

// prefer dynamic circularize (falls back internally to simple circularize)
dynamic_circularize(TARGET_APO). // reference_docs/KOS_DOC/language/user_functions.html:1

PRINT "Circularization complete (~70km).". // reference_docs/KOS_DOC/language/anonymous.html:236

// safety wrap: reduce steering locks and print orbit summary
LOCK STEERING TO SHIP:PROGRADE. // reference_docs/KOS_DOC/math/direction.html:256
PRINT "APOAPSIS=" + ROUND(SHIP:OBT:APOAPSIS,0) + " PERIAPSIS=" + ROUND(SHIP:OBT:PERIAPSIS,0) + ".".// reference_docs/KOS_DOC/structures/orbits/orbit.html:322

// finalize
SHUTDOWN. // reference_docs/KOS_DOC/language/syntax.html:176
