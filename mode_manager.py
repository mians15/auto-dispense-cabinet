
"""
Mode Manager module for the ADC.
"""
import time
from datetime import datetime


class ModeManager:

    def __init__(
        self,
        log,
        alarm_manager=None,
        fault_detector=None,
        drawer_controller=None,
        communication=None
    ):
        self.log = log

        # Connected system modules
        self.alarm_manager = alarm_manager
        self.fault_detector = fault_detector
        self.drawer_controller = drawer_controller
        self.communication = communication

        # Initial system state
        self.current = "STARTUP"
        self.fault_class = "NONE"

        # Tracks transitions for other modules
        self.on_mode_change = []


    TABLE = {
        # Startup
        ("STARTUP", "startup_ok"): "NORMAL",
        ("STARTUP", "startup_fail"): "FAULT",

        # Normal operation
        ("NORMAL", "fault"): "FAULT",
        ("NORMAL", "maint"): "MAINT",

        # Maintenance
        ("MAINT", "fault"): "FAULT",
        ("MAINT", "exit_ok"): "NORMAL",
        ("MAINT", "exit_bad"): "FAULT",

        # Fault mode
        ("FAULT", "maint"): "MAINT",
        ("FAULT", "class_a_clear"): "NORMAL",
    }


    def trigger(
        self,
        event,
        role=None,
        fault_class="B",
        safety_check_passed=False,
        fault=None
    ):
        old_mode = self.current

        # Technician-only mode changes
        if event in ("maint", "exit_ok", "exit_bad"):
            if role != "TECH":
                return False

        # Recovery from MAINT requires safety checks
        if event == "exit_ok":
            if not safety_check_passed:
                return False

        if event == "exit_bad":
            if safety_check_passed:
                return False

        # Class A faults may recover directly from FAULT
        if event == "class_a_clear":
            if self.fault_class != "A":
                return False

            if not safety_check_passed:
                return False

        # Class B faults cannot recover directly to NORMAL
        # They must go FAULT -> MAINT -> NORMAL
        if old_mode == "FAULT" and event == "class_a_clear":
            if self.fault_class == "B":
                return False

        # Find the transition
        transition = (old_mode, event)

        if transition not in self.TABLE:
            return False

        new_mode = self.TABLE[transition]

        # Update fault classification
        if event == "fault":
            self.fault_class = fault_class

        elif event == "startup_fail":
            self.fault_class = "B"

        elif event == "exit_bad":
            # Preserve existing classification where possible
            if self.fault_class == "NONE":
                self.fault_class = "B"

        elif event == "class_a_clear":
            self.fault_class = "NONE"

        elif new_mode == "NORMAL":
            self.fault_class = "NONE"

        # Update system mode
        self.current = new_mode

        # Record the mode change
        self._log_mode_change(old_mode, new_mode, event)

        # Notify connected modules
        self._handle_mode_change(old_mode, new_mode, event, fault)

        return True


    def _handle_mode_change(self, old_mode, new_mode, event, fault):

        # Entering FAULT mode
        if new_mode == "FAULT":

            # Lock every drawer
            if self.drawer_controller is not None:
                self.drawer_controller.lock_all_drawers() # CHANGE: drawercontroller method

            # Raise alarm for a detected fault
            if self.alarm_manager is not None and fault is not None:
                self.alarm_manager.raise_alarm(fault)

            # Communicate the fault state
            if self.communication is not None:
                data = {
                    "mode": "FAULT",
                    "fault_class": self.fault_class,
                    "fault": fault,
                    "time": datetime.now().isoformat()
                }

                self.communication.send("FAULT", data) #CHANGE: make it match communication method

        # Leaving FAULT mode
        if old_mode == "FAULT" and new_mode != "FAULT":

            # Clear the alarm because the system is no longer in FAULT
            if self.alarm_manager is not None:
                self.alarm_manager.clear()

        # Communicate every mode change
        if self.communication is not None:
            data = {
                "old_mode": old_mode,
                "new_mode": new_mode,
                "event": event,
                "time": datetime.now().isoformat()
            }

            self.communication.send_to_communicator("MODE_CHANGE", str(data))

        # Notify any registered callbacks
        for callback in self.on_mode_change:
            callback(old_mode, new_mode)


    def _log_mode_change(self, old_mode, new_mode, event):

        entry = {
            "type": "MODE_CHANGE",
            "old_mode": old_mode,
            "new_mode": new_mode,
            "event": event,
            "time": datetime.now().strftime("%H:%M:%S")
        }

        self.log.append(entry)


    def run_safety_check(self):

        if self.fault_detector is None:
            return False
        problems = self.fault_detector.safety_check()
        return len(problems) == 0
