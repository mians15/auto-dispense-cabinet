"""Dispenser for the ADC"""

LOW = 3

class Dispenser:
    def __init__(self, auth, inventory, hw, detector, alarms):
        self.auth = auth
        self.inventory = inventory      # find_drawer(drug), count(d), remove(d, r, user, patient_id)
        self.hw = hw                    # unlock(d), lock(d), is_open(d), removed_count(d)
        self.detector = detector
        self.alarms = alarms
        self.pending = None             # (drawer, user, drug, qty, patient_id) while a dispense is open

    def request(self, drug, qty, patient_id):
        if not self.auth.is_permitted("dispense"):    # nurse only, mode NORMAL only
            return "NOT_PERMITTED"
        if self.pending is not None:
            return "BUSY"
        if not patient_id:
            return "NO_PATIENT"
        d = self.inventory.find_drawer(drug)
        if d is None:
            return "Unavailable in this drawer."
        count = self.inventory.count(d)
        if count == 0:
            self.alarms.raise_stock_alert("OUT", d)
            return "Out of stock."
        if qty > count:
            return "Insufficient stock"

        self.hw.unlock(d)
        self.detector.watch_unlock(d, expect_removal=True)    # starts the 30 s timer
        self.pending = (d, self.auth.session[0], drug, qty, patient_id)
        return "UNLOCKED"

    def update(self):
        """Call every tick of the main loop."""
        if self.pending is None:
            return
        d, user, drug, qty, patient_id = self.pending
        removed = self.hw.removed_count(d)
        if removed > 0:
            self.detector.note_removal(d)
            before = self.inventory.count(d)
            self.inventory.remove(d, removed, user, patient_id)
            if before >= LOW and before - removed < LOW:
                self.alarms.raise_stock_alert("LOW", d)
            self.pending = None
        if not self.hw.is_open(d) and self.pending is None:
            self.hw.lock(d)                                   # lock once closed (FR_DIS_08)

    def cancel(self):
        self.pending = None                                   # controller calls this on a fault