"""
For handling the incoming ADC requests and verifies each one is authenticated.
Returns requested configuration or status information and rejects invalid requests.
"""

from .models import Result

class RequestHandler:
    def __init__(self, store, configs, adc_authentication):
        self.__store = store
        self.__configs = configs
        self.__adc_authentication = adc_authentication


    def handle(self, req, sign):
        if not isinstance(req, dict):
            return Result(False, "Invalid request format")


        # checking that request is from an authenticated ADC
        auth = self.__adc_authentication.verification(req, sign)

        if not auth.ok:
            return auth


        # if authenticated, get ID of ADC
        adc_id = auth.data["adc_id"]

        try:
            req_type = req["type"]
        except KeyError:
            return Result(False, "Missing request type")

        if not isinstance(req_type, str):
            return Result(False, "Invalid request type")


        # checking that ADC is registered in the MS
        adc = self.__store.get_adc(adc_id)

        if adc is None:
            return Result(False, "Unknown ADC")


        if req_type == "get_config":
        # ADC requests config, we return the latest approved configuration 
            return self.__configs.get_approved(adc_id)

        elif req_type == "get_status":
        # ADC requests its current status
            if not adc.connected:
                health = "Unavailable"
            else:
                health = adc.health

            return Result(True, "ADC status received", {"adc_id": adc.adc_id, "connected": adc.connected, "health": health})

        else:
        # any unsupported request
            return Result(False, "Unsupported request type")
        