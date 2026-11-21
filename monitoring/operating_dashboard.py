"""
Creating operator dashboard. Checks user permissions and can identify ADCs that aren't available or need attention.
"""

from .models import Result

class OperatorDashboard:
    def __init__(self, store, access, configurations):
        self.__store = store 
        self.__access = access
        self.__configurations = configurations

    def view(self, token):
        # checking permissions of user
        if not self.__access.authorize(token, "dashboard:view"):
            return Result(False, "Access denied")

        dashboard = []

        for adc in self.__store.list_adcs():

            # 1: Unavailable communication
            if not adc.connected:
                status = "Unavailable"
                health = "Unavailable"
                inventory = None

            # 2: ADC reports fault or health unknown
            elif adc.health != "Healthy":
                status = "Needs attention"
                health = adc.health

                if adc.inv_current:
                    inventory = adc.inv
                else:
                    inventory = None

            # 3: Inventory data is not found or old
            elif not adc.inv_current or adc.inv is None:
                status = "Inventory is unavailable"
                health = adc.health
                inventory = None

            # 4: ADC is healthy and inventory is up to date
            else:
                health = adc.health
                inventory = adc.inv

                config = self.__configurations.get_approved(adc.adc_id)

                if config.ok:
                    status = "Configuration is available"
                else:
                    try:
                        threshold = config.data["min_inv"]
                        if adc.inv <= threshold:
                            status = "Requires attention"
                        else:
                            status = "Normal"

                    except (TypeError, ValueError, KeyError):
                        # if the data for the configuration isn't as expected, don't assume ADC is normal
                        status = "Configuration is unavailable"

            dashboard.append({
                "adc_id": adc.adc_id, 
                "communication": ("Available" if adc.connected else "Unavailable"),
                "health": health, "inventory": inventory, 
                "inventory_current": (adc.inv_current and adc.connected)
            })

        return Result(True, "Dashboard filled", {"adcs": dashboard})
    