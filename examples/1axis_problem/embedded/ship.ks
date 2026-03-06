// ship.ks
// Simple KOS script for the 1‑axis rocket control example.
//
// This program reads a sequence of thrust/​throttle commands and applies
them in order while the vessel is flying.  It is intended to be run in
Kerbal Space Program with the kOS mod installed.  The commands may come
from a precomputed trajectory stored in a text file, or they may be
streamed live from a ground station using kRPC.
//
// The protocol is deliberately minimal so that it can be adapted to a
variety of situations:
//  * A plain-text file containing one floating-point value per line.
//    Each value should be in the range [0,1] and represents the throttle
//    setting for one simulation step.
//  * (Optional) a kRPC server that provides an RPC call or stream
//    named `next_thrust` which returns the next float.  When the file
//    source is not used, the script will attempt to connect and pull
//    values from kRPC until the server indicates the trajectory is done.
//
// Usage examples:
//   run ship.ks file:thrusts.txt     // read thrusts from a local file
//   run ship.ks krpc                // use kRPC stream (see below)
//   run ship.ks                     // defaults to file:thrusts.txt
//
// The file path may be absolute or relative to the kOS root
// directory (typically the kOS `ships/` folder).
//
// kRPC protocol example (python):
//   import krpc
//   conn = krpc.connect()
//   # build a generator or list of thrust commands
//   thrusts = [0.1, 0.2, 0.3, ...]
//   @conn.krpc.stream(return_type=float)
//   def next_thrust():
//       try:
//           return thrusts.pop(0)
//       except IndexError:
//           return -1.0   # signal end-of-data
//
//   # the kOS program assumes that a negative thrust value means no
//   # more commands are available and will shut itself down.
//
// NOTE: the kRPC portion is optional and only works if kRPC is
// installed and a server is running concurrently with KSP.  You can
// also replace the `get_next_thrust()` function below with your own
// communication mechanism (serial port, socket, etc.).
//
// The control loop uses a fixed time step of 1 second; adapt or replace
// the `wait` call if you need finer timing.

function read_from_file {
    parameter file_spec.
    local lst is list().
    set lst to list().
    try {
        // read every non-empty line and convert to number
        local lines is file(file_spec):readlines().
        for line in lines {
            if length(line) > 0 {
                lst:add(tofloat(line)).
            }
        }
    } catch {
        print "Error reading file "+file_spec+"?".
    }
    return lst.
}

function get_next_thrust {
    // returns next thrust value or -1 if no more data
    if source = "file" {
        if file_index > file_thrusts:length() {
            return -1.
        }
        set t to file_thrusts:file_index.
        set file_index to file_index + 1.
        return t.
    }
    if source = "krpc" {
        // this is just a stub; the user is expected to implement
        // the RPC or stream on the ground station side.  kOS can
        // call `rpc` if the connection object is stored in a global
        // variable named `krpc_conn`.
        if not defined? krpc_conn {
            print "Attempting to connect to kRPC...".
            set krpc_conn to rpc("krpc.connect").
            if not defined? krpc_conn {
                print "kRPC connection failed.".
                return -1.
            }
        }
        // call an RPC method `next_thrust` that should return a float
        local val is krpc_conn:call("next_thrust").
        if val < 0 {
            return -1.
        }
        return val.
    }
    return -1.
}

// --- main program ------------------------------------------------------

// determine source from first argument or default to file
parameter source_arg.
if not defined? source_arg {
    set source_arg to "file:thrusts.txt".
}

// parse the source
if source_arg:starts("file:") {
    set source to "file".
    set file_path to source_arg:sub(6).
    set file_thrusts to read_from_file(file_path).
    set file_index to 1.
} else if source_arg = "krpc" {
    set source to "krpc".
} else {
    print "Unrecognized source: "+source_arg+".  expected file:<path> or krpc".
    stop.
}

print "Starting ship control using source: "+source_arg.

// main loop
until false {
    local t is get_next_thrust().
    if t < 0 {
        print "No more thrust commands. exiting.".
        break.
    }
    print "Applying throttle: "+t.
    set throttle to t.
    wait 1.
}

print "Ship script finished.".
