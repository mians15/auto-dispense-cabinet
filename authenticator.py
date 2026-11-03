"""Authenticator for the ADC"""

import time
from datetime import datetime

N_FAIL = 3
T_LOCK = 5  # 5 second lockout for demo/testing (60 seconds normally)


PERMISSIONS = {
    "dispense":          ({"NURSE"},         {"NORMAL"}),
    "restock":           ({"TECH", "PHARM"}, {"NORMAL"}),
    "enter_maintenance": ({"TECH"},          {"NORMAL", "FAULT"}),
    "view_hardware":     ({"TECH"},          {"MAINT", "FAULT"}),
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

    def login(self, badge, pin):
        if self.session is not None:
            return "ALREADY_LOGGED_IN"
        mode = self.get_mode()
        user = self.users.get(badge)

        if user is None:
            return self._done(None, "UNKNOWN_BADGE")

        uid, role = user["id"], user["role"]

        if role != "TECH" and mode in ("MAINT", "FAULT"):
            return self._done(uid, "REJECTED_" + mode)

        if time.time() < self.locked_until.get(uid, 0):
            return self._done(uid, "LOCKED")

        if pin != user["pin"]:
            self.fails[uid] = self.fails.get(uid, 0) + 1
            self._done(uid, "FAIL")                         # failed attempt, always logged

            if self.fails[uid] >= N_FAIL:
                self.locked_until[uid] = time.time() + T_LOCK
                self.fails[uid] = 0
                self._done(uid, "LOCKED", "LOCKOUT")
                self.send_alert(uid)
                return "LOCKED"

            return "WRONG_PIN"
       
        self.fails[uid] = 0
        self.session = (uid, role)

        return self._done(uid, "OK")
    
    def logout(self):
        self.session = None

    def is_permitted(self, action):
        if self.session is None:
            return False
        roles, modes = PERMISSIONS.get(action, (set(), set()))
        return self.session[1] in roles and self.get_mode() in modes

    def _done(self, uid, result, event="LOGIN"):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log.append((stamp, event, uid, result))
        return result
    