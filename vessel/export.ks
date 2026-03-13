// export.ks
// This script collects telemetry about the active vessel and
// writes the information out as JSON to "vessel/export.json".
//
// The output structure looks roughly like:
// {
//   "id": <vessel name>,
//   "total_stages": <number>,
//   "current_stage": <number>,
//   "mass": <mass>,
//   "stages": [
//       {"stage":0, "fuel":..., "thrust":..., "deltaV":...},
//       ...
//   ]
// }

CLEARSCREEN.

// reference to the active ship/vessel (use built-in SHIP directly)

// basic metadata
LOCAL name IS SHIP:NAME.
LOCAL currentStageNum IS SHIP:STAGENUM.            // stage numbers count down from this
LOCAL totalStages IS currentStageNum + 1.          // simple count of stages remaining
LOCAL totalMass IS SHIP:MASS.

// lists that will be filled per stage
LOCAL stageFuel IS LIST().        // total resource amount for each stage
LOCAL stageThrust IS LIST().      // summed available thrust for each stage
LOCAL stageDeltaV IS LIST().      // delta‑V (current) for each stage

// initialize the stage arrays with zeros
LOCAL idx IS 0.
UNTIL idx > currentStageNum {
    stageFuel:PUSH(0).
    stageThrust:PUSH(0).
    stageDeltaV:PUSH(0).
    SET idx TO idx + 1.
}

// accumulate fuel amounts by examining each part's resources
LIST PARTS IN allParts.
FOR p IN allParts {
    SET s TO p:STAGE.
    // ignore parts that are not assigned or out of range
    IF s >= 0 AND s <= currentStageNum {
        // p:RESOURCES is a list of AggregateResource or Resource entries
        SET resList TO p:RESOURCES.
        FOR r IN resList {
            SET stageFuel[s] TO stageFuel[s] + r:AMOUNT.
        }
    }
}

// accumulate available thrust by examining all engines
LIST ENGINES IN allEngines.
FOR e IN allEngines {
    SET s TO e:PART:STAGE.
    IF s >= 0 AND s <= currentStageNum {
        SET stageThrust[s] TO stageThrust[s] + e:AVAILABLETHRUST.
    }
}

// query deltaV struct for each stage
SET idx TO 0.
UNTIL idx > currentStageNum {
    SET stageDeltaV[idx] TO SHIP:STAGEDELTAV(idx):CURRENT.
    SET idx TO idx + 1.
}

// build the JSON-able object
LOCAL data IS LEXICON().
data:ADD("id", name).
data:ADD("total_stages", totalStages).
data:ADD("current_stage", currentStageNum).
data:ADD("mass", totalMass).

// create list of stage info lexicons
LOCAL stages IS LIST().
SET idx TO 0.
UNTIL idx > currentStageNum {
    LOCAL st IS LEXICON().
    st:ADD("stage", idx).
    st:ADD("fuel", stageFuel[idx]).
    st:ADD("thrust", stageThrust[idx]).
    st:ADD("deltaV", stageDeltaV[idx]).
    stages:PUSH(st).
    SET idx TO idx + 1.
}

data:ADD("stages", stages).

// ensure the output directory exists
IF NOT EXISTS("vessel") {
    CREATEDIR("vessel").
}

// write the JSON file
WRITEJSON(data, "vessel/export.json").

PRINT "export.ks: telemetry written to vessel/export.json".
