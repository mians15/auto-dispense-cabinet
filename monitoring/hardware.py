"""Simulated hardware for the ADC: drawer locks and drawer sensors.

"""

import time


class Hardware:
    def __init__(self, drawers):
        self.drawers = drawers
        self.open_state = {}       
        self.lock_status = {}      
        self.taken = {}            
        self.jammed = []           
        self.dead_since = {}       
        for d in drawers:
            self.open_state[d] = False
            self.lock_status[d] = "LOCKED"
            self.taken[d] = 0

    def is_open(self, d):
        return self.open_state[d]

    def lock_state(self, d):
        """"LOCKED", "UNLOCKED", or None when the lock gives no feedback."""
        if d in self.jammed:
            return None
        return self.lock_status[d]

    def last_reading(self, d):
        """Time of the sensor's latest reading. A dead sensor stops updating."""
        if d in self.dead_since:
            return self.dead_since[d]
        return time.time()

    def unlock(self, d):
        if d not in self.jammed:
            self.lock_status[d] = "UNLOCKED"
        self.taken[d] = 0

    def lock(self, d):
        if d not in self.jammed:
            self.lock_status[d] = "LOCKED"

    def removed_count(self, d):
        return self.taken[d]

    # SIMULATION
    def open_drawer(self, d):
        """A drawer can only be opened if its lock is unlocked."""
        if self.lock_state(d) != "UNLOCKED":
            return False
        self.open_state[d] = True
        return True

    def take_dose(self, d):
        """A dose can only be taken from an open drawer."""
        if not self.open_state[d]:
            return False
        self.taken[d] = self.taken[d] + 1
        return True

    def close_drawer(self, d):
        self.open_state[d] = False

    def jam_lock(self, d):
        if d not in self.jammed:
            self.jammed.append(d)

    def kill_sensor(self, d):
        if d not in self.dead_since:
            self.dead_since[d] = time.time()

    def repair_all(self):
        self.jammed = []
        self.dead_since = {}

    def describe(self):
        text = ""
        for d in self.drawers:
            if self.open_state[d]:
                door = "open"
            else:
                door = "closed"
            lock = self.lock_state(d)
            if lock is None:
                lock = "NO FEEDBACK"
            text = text + "[drawer " + str(d) + ": " + door + ", " + lock + "]  "
        return text