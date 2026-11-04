""" Fault detector module for the ADC"""

import time

T_RESP = 3      # seconds 

# fault type 
# "A" clears itself, "B" needs a technician
CLASS_OF = {
    "DRAWER_OPEN": "A",
    "NO_REMOVAL":  "A",
    "LOCK_SILENT": "B",
    "SENSOR_DEAD": "B",
    "SOFTWARE":    "B",
}


class FaultDetector:
    def __init__(self, drawers, hw):
        self.drawers = drawers
        self.hw = hw                  
        self.unlocked = {}          
        self.removed = set()          
        self.lock_cmds = {}          
        self.active = {}             


    def watch_unlock(self, d, expect_removal=True):
        self.unlocked[d] = (time.time(), expect_removal)
        self.removed.discard(d)

    def note_removal(self, d):
        self.removed.add(d)

    def watch_lock_command(self, d, expected):
        self.lock_cmds[d] = (expected, time.time())

    def report_software_failure(self, detail=""):
        new = []
        self._report("SOFTWARE", None, new)
        return new

    # returns new faults
    def poll(self):
        now = time.time()
        new = []

        for d, (t0, expect) in list(self.unlocked.items()):
            is_open = self.hw.is_open(d)
            if not is_open and (d in self.removed or not expect):
                del self.unlocked[d]                       # finished normally
                continue
            if now - t0 >= T_RESP:
                if is_open:
                    self._report("DRAWER_OPEN", d, new)    # drawer left open
                if expect and d not in self.removed:
                    self._report("NO_REMOVAL", d, new)     # no removal detected
                if not is_open:
                    del self.unlocked[d]

        for d, (expected, t0) in list(self.lock_cmds.items()):
            if self.hw.lock_state(d) == expected:
                del self.lock_cmds[d]
            elif now - t0 >= T_RESP:
                del self.lock_cmds[d]
                self._report("LOCK_SILENT", d, new)        

        for d in self.drawers:
            if now - self.hw.last_reading(d) >= T_RESP:
                self._report("SENSOR_DEAD", d, new)       

        return new

    def clear_resolved(self):
        """Class A faults whose drawer is now closed are cleared. Returns them."""
        cleared = []
        for key, f in list(self.active.items()):
            if f[1] == "A" and not self.hw.is_open(f[2]):
                del self.active[key]
                self.unlocked.pop(f[2], None)      # stop watching this drawer
                cleared.append(f)
        return cleared
   

    def safety_check(self):
        """Empty list means it passed, every lock/sensor responds, all drawers closed and locked."""
        now = time.time()
        problems = []
        for d in self.drawers:
            if now - self.hw.last_reading(d) >= T_RESP:
                problems.append(("SENSOR_DEAD", d))
            if self.hw.lock_state(d) != "LOCKED":
                problems.append(("LOCK_NOT_LOCKED", d))
            if self.hw.is_open(d):
                problems.append(("DRAWER_OPEN", d))
        if not problems:
            self.active.clear()
        return problems

    def _report(self, kind, d, new):
        key = (kind, d)
        if key not in self.active:                         # report each fault once
            fault = (kind, CLASS_OF[kind], d)
            self.active[key] = fault
            new.append(fault)