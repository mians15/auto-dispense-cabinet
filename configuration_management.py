"""
Hides configuration storage, approval rules, and version selection.
"""

from .models import Configuration, Result

class ConfigurationManagement:
    def __init__(self, store):
        self.__store = store
        self.__configs = {}


    def register(self, config):
        if not isinstance(config, Configuration):
        # making sure object is part of Config class
            return Result(False, "Invalid configuration object")

        # checking ADC exists
        if self.__store.get_adc(config.adc_id) is None:
            return Result(False, "Unknown ADC")

        try:
            saved = Configuration(
                config.adc_id, config.version, config.approved, config.min_inv, config.med_sched)
            # creating new object to validate its values to prevent the user from changing info of original config to invalid values

        except (ValueError, TypeError) as error:
            return Result(False, "Invalid configuration: " + str(error))

        if saved.adc_id not in self.__configs:
        # one ADC can have multiple configurations so if its not already there, then initialize and add it in the configs dictionary
            self.__configs[saved.adc_id] = []

        # dont allow duplicate version number
        for duplicate in self.__configs[saved.adc_id]:
            if duplicate.version == saved.version:
                return Result(False, "Duplicate configuration version")

        self.__configs[saved.adc_id].append(saved)
        # get list of configs for that ADC then append the append the new config to that list

        return Result(True, "Configuration registered")


    def get_approved(self, adc_id):
        if not isinstance(adc_id, str):
            return Result(False, "Invalid ADC ID")

        if self.__store.get_adc(adc_id) is None:
            return Result(False, "Unkown ADC")

        configs = self.__configs.get(adc_id, [])
        # getting the specific ADC's configs, if none found, defaults to []

        latest = None   # initializing

        for config in configs:
            if config.approved:
            # approved is one of the attributes of a Configuration object
                if latest is None or config.version > latest.version:
                # loop through to find latest configuration version
                # "if latest is None" is for the first condition from when we initialized latest
                    latest = config

        if latest is None:
        # once loop is done, if there wasnt something in the configs list, latest will still be None
            return Result(False, "No approved configuration")

        return Result(True, "Approved configuration found", {
            "adc_id": latest.adc_id, "version": latest.version, "min_inv": latest.min_inv, "med_sched": list(latest.med_sched)
            })
        # made a copied list of the med_sched so the user cant directly access the med_sched
    