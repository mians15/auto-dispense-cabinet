"""Inventory module for the ADC: which drug is in which drawer, and how many doses are left."""

from datetime import datetime

CAP = 10 # max doses a drawer can hold


def stamp():
    return datetime.now().strftime("%H:%M:%S")


class Inventory:
    def __init__(self):
        self.drawer_of = {"morphine": 1, "insulin": 2}     # drug -> drawer
        self.counts = {1: 5, 2: 3}                         # drawer -> doses left
        self.records = []                                  # inventory log

    def find_drawer(self, drug):
        """Drawer number for a drug, or None if the cabinet does not stock it."""
        return self.drawer_of.get(drug)

    def count(self, d):
        return self.counts[d]

    def remove(self, d, n, user, patient_id):
        """Doses were dispensed. The count never goes below 0."""
        self.counts[d] = self.counts[d] - n
        if self.counts[d] < 0:
            self.counts[d] = 0
        self.records.append((stamp(), "DISPENSE", user,
                             "drawer " + str(d) + " x" + str(n) + " patient " + patient_id))

    def add(self, d, n, user):
        """Doses were restocked. Returns False (and changes nothing) if the drawer would overflow."""
        if self.counts[d] + n > CAP:
            self.records.append((stamp(), "RESTOCK", user, "drawer " + str(d) + " +" + str(n) + " REJECTED"))
            return False
        self.counts[d] = self.counts[d] + n
        self.records.append((stamp(), "RESTOCK", user, "drawer " + str(d) + " +" + str(n)))
        return True