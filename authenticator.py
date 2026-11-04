"""Authenticator for the ADC"""

import time
from datetime import datetime

# Constants from Deliverable 2
N_FAIL = 3
T_LOCK = 5  # seconds, 5 for demo/test, 60 actual

# Permissions based on the Deliverable 2 permissions table
PERMISSIONS = {
    "dispense": (
        {"NURSE"},
        {"NORMAL"}
    ),

    "restock": (
        {"TECH", "PHARM"},
        {"NORMAL"}
    ),

    "enter_maintenance": (
        {"TECH"},
        {"NORMAL", "FAULT"}
    ),

    "view_hardware": (
        {"TECH"},
        {"MAINT", "FAULT"}
    ),
}

class Authenticator:
    def __init__(self, users, log, get_mode, send_alert):
        self.users = users
        self.log = log
        self.get_mode = get_mode
        self.send_alert = send_alert

        self.fails = {}
        self.locked_until = {}
        self.session = None

    def _login(self, badge, pin):
        # Only one active session is permitted
        if self.session is not None:
            return "ALREADY_LOGGED_IN"

        mode = self.get_mode()
        user = self.users.get(badge)

        # Unknown badge, record FAIL and return result
        if user is None:
            self._done(None, "FAIL")
            return "UNKNOWN_BADGE"

        uid = user["id"]
        role = user["role"]

        # Validate user role
        if role not in ("NURSE", "PHARM", "TECH"):
            self._done(uid, "FAIL")
            return "INVALID_ROLE"

        # Only technicians may authenticate in MAINT or FAULT
        if role != "TECH" and mode in ("MAINT", "FAULT"):
            self._done(uid, "FAIL")
            if mode == "MAINT":
                return "Cabinet in maintenance mode"
            elif mode == "FAULT":
                return "Cabinet in fault mode"
            

        current_time = time.time()
        lock_until = self.locked_until.get(uid, 0)

        # Check whether the user is still locked out
        if current_time < lock_until:
            self._done(uid, "LOCKED")
            return "LOCKED"

        # Lockout has expired: reset the failure counter
        if lock_until != 0:
            self.locked_until[uid] = 0
            self.fails[uid] = 0

        # Incorrect PIN
        if pin != user["pin"]:
            self.fails[uid] = self.fails.get(uid, 0) + 1

            # Third consecutive failed attempt
            if self.fails[uid] >= N_FAIL:
                self.locked_until[uid] = current_time + T_LOCK
                self.fails[uid] = 0

                # One log entry for this login attempt
                self._done(uid, "LOCKED")

                # Trigger security alert
                self.send_alert(uid)

                return "LOCKED"

            # Log failed attempt
            self._done(uid, "FAIL")
            return "WRONG_PIN"

        # Successful login
        self.fails[uid] = 0
        self.locked_until[uid] = 0
        self.session = (uid, role)

        self._done(uid, "SUCCESS")
        return "SUCCESS"

    def login(self, badge, pin):
        self._login(badge, pin)

    def logout(self):
        self.session = None

    def is_permitted(self, action):
        # No active session means no permission
        if self.session is None:
            return False

        roles, modes = PERMISSIONS.get(
            action,
            (set(), set())
        )

        user_role = self.session[1]
        current_mode = self.get_mode()

        return (
            user_role in roles
            and current_mode in modes
        )
    
    def _done(self, uid, result):
        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        # Append one authentication log record
        self.log.append(
            (
                timestamp,
                "LOGIN",
                uid,
                result
            )
        )

        return result
