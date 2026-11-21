"""Inventory tracking backed by shared ADC records."""
from .models import Result

class InventorySupervision:
    def __init__(self, store, access, configurations):
        self.__store = store
        self.__access = access
        self.__configurations = configurations

    def __threshold(self, adc_id):
        """Return (threshold, error). Never invent a default configuration."""
        result = self.__configurations.get_approved(adc_id)
        if not result.ok:
            return None, result.message
        return result.data["min_inv"], None

    def receive_inventory(self, adc_id, quantity):
        """Called with an already authenticated ADC identity."""
        if self.__store.get_adc(adc_id) is None:
            return Result(False, "Unknown ADC")
        if type(quantity) is not int or quantity < 0:
            self.__store.update_adc(adc_id, inv_current=False)
            self.__store.log("invalid_inventory", f"{adc_id}: invalid quantity")
            return Result(False, "Invalid inventory quantity")
        result = self.__store.update_adc(adc_id, inv=quantity, inv_current=True)
        if result.ok:
            self.__store.log("inventory_updated", f"{adc_id}: quantity={quantity}")
            threshold, error = self.__threshold(adc_id)
            if error is not None:
                self.__store.log("inventory_threshold_unavailable", f"{adc_id}: {error}")
            elif quantity < threshold:
                self.__store.log("low_inventory", f"{adc_id}: quantity={quantity}, minimum={threshold}")
        return result

    def mark_unavailable(self, adc_id):
        result = self.__store.update_adc(adc_id, inv_current=False)
        if result.ok:
            self.__store.log("inventory_unavailable", adc_id)
        return result

    def view(self, token, adc_id=None):
        if not self.__access.authorize(token, "inventory:view"):
            return Result(False, "Access denied")
        adcs = [self.__store.get_adc(adc_id)] if adc_id is not None else self.__store.list_adcs()
        if any(adc is None for adc in adcs):
            return Result(False, "Unknown ADC")
        rows = []
        for adc in adcs:
            current = adc.connected and adc.inv_current
            threshold, error = self.__threshold(adc.adc_id)
            if not current:
                status = "Unavailable"
            elif error is not None:
                status = "Threshold unavailable"
            elif adc.inv < threshold:
                status = "Requires attention"
            else:
                status = "Normal"
            rows.append({"adc_id": adc.adc_id, "quantity": adc.inv,
                         "current": current, "minimum": threshold,
                         "status": status})
        return Result(True, "Inventory records", {"inventory": rows})
