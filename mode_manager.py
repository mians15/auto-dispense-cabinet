""" Mode manager for ADC"""
from datetime import datetime

# Mode transition table based on Deliverable 2 (T1-T9)
TABLE = {
    ("STARTUP", "startup_ok"): "NORMAL",  # T1
    ("STARTUP", "startup_bad"): "FAULT",  # T2

    ("NORMAL", "fault"): "FAULT",         # T3
    ("NORMAL", "maint"): "MAINT",         # T4

    ("MAINT", "fault"): "FAULT",          # T5
    ("MAINT", "exit_ok"): "NORMAL",       # T6
    ("MAINT", "exit_bad"): "FAULT",       # T7

    ("FAULT", "a_cleared"): "NORMAL",     # T8
    ("FAULT", "maint"): "MAINT",          # T9

    # Remain in FAULT if another fault is detected
    ("FAULT", "fault"): "FAULT",
}


class ModeManager:
    def __init__(self, log):
        self.log = log
        self.mode = "STARTUP"
        self.fault_class = "NONE"
        self.change_handler = []

    def current(self):
        return self.mode

    def on_mode_change(self, fn):
        self.change_handler.append(fn)

    def trigger(
        self,
        event,
        role=None,
        fault_class="B",
        safety_check_passed=False
    ):
        key = (self.mode, event)

        if key not in TABLE:
            raise ValueError(
                f"Invalid transition: {self.mode} -> {event}"
            )

        # T4 and T9: Only a technician may enter Maintenance
        if event == "maint" and role != "TECH":
            raise ValueError(
                "Only TECH can enter Maintenance mode"
            )

        # T6 and T7: Only a technician may exit Maintenance
        if event in ("exit_ok", "exit_bad") and role != "TECH":
            raise ValueError(
                "Only TECH can exit Maintenance mode"
            )

        # T6: Technician exits Maintenance after passing checks
        if event == "exit_ok" and not safety_check_passed:
            raise ValueError(
                "Safety checks must pass before returning to NORMAL"
            )

        # T8: Only class A faults may recover directly to NORMAL after the fault is cleared and safety checks pass
        if event == "a_cleared":
            if self.fault_class != "A":
                raise ValueError(
                    "Only class A faults can recover directly to NORMAL"
                )

            if not safety_check_passed:
                raise ValueError(
                    "Safety checks must pass before fault recovery"
                )

        # Update fault classification
        # Class B takes priority over class A
        if event in ("fault", "startup_bad", "exit_bad"):
            if fault_class not in ("A", "B"):
                raise ValueError("Fault class must be A or B")

            if self.fault_class == "B" or fault_class == "B":
                self.fault_class = "B"
            else:
                self.fault_class = "A"

        old_mode = self.mode
        new_mode = TABLE[key]

        if new_mode != old_mode:
            self.mode = new_mode

            # Clear fault classification upon successful recovery
            if new_mode == "NORMAL":
                self.fault_class = "NONE"

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # Append one mode-change log entry
            self.log.append(
                (
                    timestamp,
                    "MODE_CHANGE",
                    None,
                    f"{old_mode}->{new_mode}"
                )
            )

            # Notify modules
            for fn in self.change_handler:
                fn(old_mode, new_mode)

        return self.mode
