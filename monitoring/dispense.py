"""Dispenser for the ADC """

LOW = 3


class Dispenser:
    def __init__(self, auth, inventory, hw, detector, alarms):
        self.auth = auth
        self.inventory = inventory      # find_drawer(drug), count(d), remove(d, n, user, patient_id)
        self.hw = hw                    
        self.detector = detector
        self.alarms = alarms
        self.pending = None            
        self.opened = False            

    def request(self, drug, qty, patient_id):
        """Returns a result code. The UI turns it into text."""
        if not self.auth.is_permitted("dispense"):    # nurse only, mode NORMAL only
            return "NOT_PERMITTED"
        if self.pending is not None:
            return "BUSY"
        if not patient_id:
            return "NO_PATIENT"
        d = self.inventory.find_drawer(drug)
        if d is None:
            return "UNAVAILABLE"
        count = self.inventory.count(d)
        if count == 0:
            self.alarms.raise_stock_alert(d, drug, count, "OUT")
            return "OUT_OF_STOCK"
        if qty < 1 or qty > count:
            return "INSUFFICIENT"

        self.hw.unlock(d)
        self.detector.watch_unlock(d, True)                   
        self.detector.watch_lock_command(d, "UNLOCKED")       
        self.pending = (d, self.auth.session[0], drug, qty, patient_id)
        self.opened = False
        return "UNLOCKED"

    def update(self):
        """Call every tick of the main loop."""
        if self.pending is None:
            return
        d, user, drug, qty, patient_id = self.pending

        if self.hw.removed_count(d) > 0:
            self.detector.note_removal(d)                     # stops the 'no removal' fault
        if self.hw.is_open(d):
            self.opened = True
            return                                            # wait until the drawer is closed
        if not self.opened:
            return                                            # not opened yet

        # the drawer was opened and is now closed: record what was taken, then lock it
        removed = self.hw.removed_count(d)
        if removed > 0:
            before = self.inventory.count(d)
            self.inventory.remove(d, removed, user, patient_id)
            if before >= LOW and before - removed < LOW:
                self.alarms.raise_stock_alert(d, drug, before - removed, "LOW")
        self.hw.lock(d)                                       
        self.detector.watch_lock_command(d, "LOCKED")
        self.pending = None

    def cancel(self):
        self.pending = None    

        