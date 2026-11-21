"""Cabinet health uses MonitoringStorage; offline is never healthy."""
from .models import Result

class CabinetHealthMonitoring:
    def __init__(self, store, access):
        self.__store = store
        self.__access = access

    def receive_health(self, adc_id, health):
        """Called after authentication by ADCCommunication."""
        if health not in ("Healthy", "Fault", "Maintenance"):
            return Result(False, "Invalid health value")
        result = self.__store.update_adc(adc_id, health=health)
        if result.ok:
            self.__store.log("health_updated", f"{adc_id}: {health}")
        return result

    def view(self, token, adc_id=None):
        if not self.__access.authorize(token, "health:view"):
            return Result(False, "Access denied")
        adcs = [self.__store.get_adc(adc_id)] if adc_id is not None else self.__store.list_adcs()
        if any(adc is None for adc in adcs):
            return Result(False, "Unknown ADC")
        rows = [{"adc_id": adc.adc_id, "connected": adc.connected,
                 "health": adc.health if adc.connected else "Unavailable",
                 "last_known_health": adc.health} for adc in adcs]
        return Result(True, "Cabinet health records", {"cabinets": rows})
