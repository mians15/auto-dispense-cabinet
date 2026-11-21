"""
Used to manage ADC authentication. Creates secret keys, verifies requests, and doesn't allow duplicate requests.
"""

import hashlib, hmac, json, secrets
# hashlib has hashing algorithm
# hmac creates and checks secure signatures
# json is to make dictionaries have a consistent format
# secrets makes random keys

from .models import Result

class ADCAuthentication:
    def __init__(self):
        self.__keys = {}
        self.__used_reqs = {}


    def register_adc(self, adc_id):
        if not isinstance(adc_id, str) or not adc_id.strip():
            return Result(False, "Invalid ADC ID")

        if adc_id in self.__keys:
            return Result(False, "ADC already has a key")

        secret = secrets.token_bytes(32)
        # generates 32 random bytes

        self.__keys[adc_id] = secret 
        self.__used_reqs[adc_id] = set()
        # making an empty set (group w/o duplicates) of an ADC's used req IDs

        return Result(True, "ADC authentication has been registered", {"secret": secret})


    def make_sign(self, secret, req):
        message = json.dumps(req, sort_keys=True).encode()
        # json.dumps(req) makes the dictionary into a json-formatted str
        # sort_keys keeps keys of the dictionary are ordered in alphabetical order
        # .encode then makes the json str into bytes

        return hmac.new(secret, message, hashlib.sha256).hexdigest()
        # using sha256 we're making an hmac with the ADC's secret and message 
        # then hexdigest turns the hmac into a hexadecimal str 


    def verification(self, req, sign):
        if not isinstance(req, dict):
            return Result(False, "Invalid request")

        if not isinstance(sign, str):
            return Result(False, "Invalid signature")

        adc_id = req.get("adc_id")
        req_id = req.get("req_id")

        if not isinstance(adc_id, str) or adc_id not in self.__keys:
            return Result(False, "Unknown ADC")

        if not isinstance(req_id, str) or not req_id:
            return Result(False, "Invalid request ID")

        if req_id in self.__used_reqs[adc_id]:
            return Result(False, "Request already used")

        try:
            expected = self.make_sign(self.__keys[adc_id], req)
            # making a new signature to know what we should expect from an ADC if it gives the right key and the req wasn't modified
        except (ValueError, TypeError, UnicodeError):
            return Result(False, "Invalid request data")

        if not hmac.compare_digest(sign, expected):
        # comparing the given signature with the one we calculated to verify that they're identical
            return Result(False, "ADC authentication failed")

        self.__used_reqs[adc_id].add(req_id)
        # adding the approved request's id to the dictionary so it isn't repeated later

        return Result(True, "ADC authenticated", {"adc_id": adc_id})