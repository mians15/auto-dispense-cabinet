"""A simple mode manager for the ADC"""

from datetime import datetime

# M1 as data: (current mode, event) -> next mode
TABLE = {
    ("STARTUP", "startup_ok"):  "NORMAL",   # T1
    ("STARTUP", "startup_bad"): "FAULT",    # T2
    ("NORMAL",  "fault"):       "FAULT",    # T3
    ("NORMAL",  "maint"):       "MAINT",    # T4
    ("MAINT",   "fault"):       "FAULT",    # T5
    ("MAINT",   "exit_ok"):     "NORMAL",   # T6
    ("MAINT",   "exit_bad"):    "FAULT",    # T7
    ("FAULT",   "a_cleared"):   "NORMAL",   # T8
    ("FAULT",   "maint"):       "MAINT",    # T9
    ("FAULT",   "fault"):       "FAULT",    # another fault while already in FAULT
}


class ModeManager:
    def __init__(self, log):
        self.log = log
        self.mode = "STARTUP"
        self.fault_class = "NONE"          # "NONE", "A" or "B"
        self.change_handler = []

    def current(self):
        return self.mode

    def on_mode_change(self, fn):
        self.change_handler.append(fn)    # fn(old_mode, new_mode)

    def trigger(self, event, role=None, fault_class="B"):
        key = (self.mode, event)
        if key not in TABLE:
            raise ValueError(f"{event} not allowed in {self.mode}")

        if event == "maint" and role != "TECH":       
            raise ValueError("only a technician can enter maintenance")

        if event == "a_cleared" and self.fault_class != "A":
            return self.mode                           # class B active: no change 

        if event in ("fault", "startup_bad", "exit_bad"):
            # class B overrides class A
            self.fault_class = "B" if "B" in (fault_class, self.fault_class) else "A"

        old, new = self.mode, TABLE[key]
        if new == "NORMAL":
            self.fault_class = "NONE"                  # NORMAL never with class B

        if new != old:                                 # log and notify real changes only
            self.mode = new
            stamp = datetime.now().strftime("%H:%M:%S")
            self.log.append((stamp, "MODE_CHANGE", None, f"{old}->{new}"))
            for fn in self.change_handler:
                fn(old, new)
        return self.mode