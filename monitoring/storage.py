"""
Hides the internal storage of alarms, event records, and ADCs.
"""

from datetime import datetime, timezone
from .models import ADC, Result

class MonitoringStorage:
    def __init__(self):
        self.__adcs = {}
        self.__alarms = {}
        self.__events = []
        # dictionaries for ADCs and alarms because they're good to look things up by ID
        # list for events because we want to keep them in order


    def register_adc(self, adc_id):
        try:
            if adc_id in self.__adcs:
                return Result(False, "Already registered")

            adc = ADC(adc_id)
            self.__adcs[adc_id] = adc   # adds ADC ID to dictionary

            return Result(True, "ADC is now registered")

        except (ValueError, TypeError) as error:
            return Result(False, "Couldn't register: " + str(error))


    def get_adc(self, adc_id):
        # Returns a copy so caller can't modify the stored ADCs
        adc = self.__adcs.get(adc_id)

        if adc is None:
            return None

        return ADC(adc.adc_id, adc.connected, adc.health, adc.inv, adc.inv_current)


    def list_adcs(self):
        adcs = []

        for adc_id in self.__adcs:
            adcs.append(self.get_adc(adc_id))

        return adcs


    def update_adc(self, adc_id, **changes):
        # stars make all the extra arguments part of a dictionary called changes
        adc = self.__adcs.get(adc_id)

        if adc is None:
            return Result(False, "Unknown ADC")

        allowed = ["connected", "health", "inv", "inv_current"]

        for field in changes:
        # Used to reject invalid fields before the change is made
            if field not in allowed:
                return Result(False, "Invalid ADC field: " + field)

        # Make a new object with the values
        #    but if validation does not work, keep things unchanged
        try:
            new_adc = ADC(adc.adc_id, changes.get("connected", adc.connected),
                          changes.get("health", adc.health), 
                          changes.get("inv", adc.inv),
                          changes.get("inv_current", adc.inv_current))
            # rerunning ADC so its __init__ can run so it can check if the inputs are valid

            self.__adcs[adc_id] = new_adc   
            # only happens if the ADC is valid so the original is never lost even if an error occurs
            
            return Result(True, "ADC has been updated")

        except (ValueError, TypeError) as error:
            return Result(False, "Invalid update: " + str(error))


    def log(self, event_type, description):
        event = {
            "time": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "description": description
        }

        self.__events.append(event)


    def get_events(self):
        return [event.copy() for event in self.__events]


    def save_alarm(self, alarm_id, adc_id, message):
        if not isinstance(alarm_id, str) or not alarm_id.strip():
            # if its not a string or its an empty string
            return Result(False, "Invalid alarm ID")

        if not isinstance(message, str) or not message.strip():
            return Result(False, "Invalid alarm message")

        if adc_id not in self.__adcs:
            return Result(False, "Unknown ADC")

        if alarm_id in self.__alarms:
            return Result(False, "Duplicate alarm ID")

        self.__alarms[alarm_id] = {
            "alarm_id": alarm_id,
            "adc_id": adc_id,
            "message": message,
            "state": "Active",  # alarm starts as Active at first, always
            "acknowledged_by": None
        }

        return Result(True, "Alarm saved")


    def get_alarm(self, alarm_id):
        alarm = self.__alarms.get(alarm_id)

        if alarm is None:
            return None

        return alarm.copy()


    def list_alarms(self):
        return [alarm.copy() for alarm in self.__alarms.values()]


    def update_alarm(self, alarm_id, state, acknowledged_by=None):
        alarm = self.__alarms.get(alarm_id)

        if alarm is None:
            return Result(False, "Unknown alarm")

        current = alarm["state"]    
        # alarm is a dictionary so here we are getting the value stored with "state"

        valid = (
            (current == "Active" and state in ["Acknowledged", "Resolved"]) 
            or (current == "Acknowledged" and state == "Resolved")
            )

        if not valid:
            return Result(False, "Invalid alarm state transition")

        alarm["state"] = state
        # changing the value to the state specified by user

        if acknowledged_by is not None:
            alarm["acknowledged_by"] = acknowledged_by

        return Result(True, "Alarm updated")
    