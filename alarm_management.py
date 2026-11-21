"""Alarm lifecycle. Call receive_alarm only after ADC authentication."""
from .models import Result

class AlarmManagement:
    def __init__(self, store, access):
        self.__store = store
        self.__access = access

    def receive_alarm(self, adc_id, alarm_id, message):
        result = self.__store.save_alarm(alarm_id, adc_id, message)
        if result.ok:
            self.__store.log("alarm_received", f"{adc_id}: {alarm_id}: {message}")
        else:
            self.__store.log("invalid_alarm", f"{adc_id}: {alarm_id}: {result.message}")
        return result

    def view(self, token, active_only=False):
        if not self.__access.authorize(token, "alarms:view"):
            return Result(False, "Access denied")
        alarms = self.__store.list_alarms()
        if active_only:
            alarms = [a for a in alarms if a["state"] != "Resolved"]
        return Result(True, "Alarm records", {"alarms": alarms})

    def acknowledge(self, alarm_id, token):
        if not self.__access.authorize(token, "alarms:acknowledge"):
            return Result(False, "Access denied")
        alarm = self.__store.get_alarm(alarm_id)
        if alarm is None:
            return Result(False, "Unknown alarm")
        if alarm["state"] != "Active":
            return Result(False, "Alarm is not Active")
        username = self.__access.get_username(token)
        result = self.__store.update_alarm(alarm_id, "Acknowledged", username)
        if result.ok:
            self.__store.log("alarm_acknowledged", f"{alarm_id} by {username}")
        return result

    def clear(self, alarm_id):
        """Trusted ADC clearance event only; caller authenticates the ADC first."""
        alarm = self.__store.get_alarm(alarm_id)
        if alarm is None:
            return Result(False, "Unknown alarm")
        result = self.__store.update_alarm(alarm_id, "Resolved")
        if result.ok:
            self.__store.log("alarm_resolved", f"{alarm_id} from {alarm['adc_id']}")
        return result
