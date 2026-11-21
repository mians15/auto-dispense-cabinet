"""
Link between the ADC's Communication module and the Hospital Monitoring System .

Communication already queues messages, retries them and reports "offline". It hands each
message, as text ("SOURCE: message"), to a monitor object's send(). This class is that monitor
object, but backed by the real Monitoring System instead of the demo stand-in.

It is the only place that knows the Monitoring System's message format. If Part B changes its
messages, only _translate() and _alarm_text() change.

"""

import ast
import uuid
from monitoring.models import Configuration


# ADC mode -> health value the Monitoring System accepts
HEALTH_OF_MODE = {"NORMAL": "Healthy", "MAINT": "Maintenance", "FAULT": "Fault"}


class MonitorLink:
    def __init__(self, app, adc_id="ADC-01"):
        self.app = app
        self.adc_id = adc_id
        self.secret = None
        self.online = True            # demo network switch
        self.need_check = False       # send connection_check before the next message
        self.alarm_number = 0
        self.rejected = []            # (message type, reason) the Monitoring System refused
        self.token = None             # login used to show the Monitoring System in the demo

    def register(self, min_inv=3):
        """Demo only: in a hospital, Part B registers the ADC and approves its configuration beforehand."""
        self.app.store.register_adc(self.adc_id)
        result = self.app.adc_authentication.register_adc(self.adc_id)
        if not result.ok:
            return False
        self.secret = result.data["secret"]
        config_result = self.app.configurations.register(
            Configuration(self.adc_id, 1, True, min_inv, [])
        )

        #print("CONFIG REGISTER:", config_result.ok, config_result.message)

        approved_result = self.app.configurations.get_approved(self.adc_id)

        #print("CONFIG LOOKUP:", approved_result.ok, approved_result.message)

        if approved_result.ok:
            print(approved_result.data)

        self.app.access.add_user("admin_demo", "password", "administrator")
        self._deliver("connection_check", {})
        return True

    def send(self, text):
        """Returns True once the Monitoring System has answered (even if it refused the message),
        and False when there was no answer, so Communication keeps the message and retries."""
        if not self.online:
            return False
        if self.need_check:                                  # first contact after a break
            if self._deliver("connection_check", {}) is None:
                return False
            self.need_check = False
        source, separator, body = text.partition(": ")
        translated = self._translate(source, body)
        if translated is None:
            return True                                      # nothing to tell the Monitoring System
        return self._deliver(translated[0], translated[1]) is not None

    def set_online(self, up):
        if up == self.online:
            return
        if up:
            self.online = True
            self.need_check = True
        else:
            self._deliver("disconnect", {})    # demo only: a real cable pull cannot announce itself
            self.online = False

    def _translate(self, source, body):
        """Returns (message type, fields), or None if the Monitoring System has no use for it."""
        try:
            if source == "MODE":
                mode = body.split()[-1]                      # "Mode changed to FAULT"
                if mode in HEALTH_OF_MODE:
                    return ("health", {"health": HEALTH_OF_MODE[mode]})
                return None
            if source == "INVENTORY":
                return ("inventory", {"quantity": int(body)})
            if source in ("ALARM", "MAINTENANCE_REQUEST", "SECURITY_ALERT", "STOCK_ALERT"):
                data = ast.literal_eval(body)
                self.alarm_number = self.alarm_number + 1
                return ("alarm", {"alarm_id": "ALM-%03d" % self.alarm_number,
                                  "message": self._alarm_text(source, data)})
            if source == "ACCESS_LOG":
                data = ast.literal_eval(body)

                return ("access_log", {
                    "badge": data["badge"],
                    "result": data["result"],
                    "time": data["time"]
                })
        except (ValueError, SyntaxError, KeyError, IndexError):
            self.rejected.append((source, "could not read the message"))
        return None       
    def _alarm_text(self, source, data):
        if source == "ALARM":
            text = "Fault " + data["kind"] + " (class " + data["class"] + ")"
        elif source == "MAINTENANCE_REQUEST":
            text = "Maintenance required: " + data["kind"]
        elif source == "SECURITY_ALERT":
            return "Security alert: user " + data["user_id"] + " locked out"
        elif data["type"] == "OUT":
            return "Out of stock: " + data["drug"] + " in drawer " + str(data["drawer"])
        else:
            return ("Low stock: " + data["drug"] + " in drawer " + str(data["drawer"]) +
                    " has " + str(data["count"]) + " doses")
        if data["drawer"] is not None:
            text = text + " on drawer " + str(data["drawer"])
        return text

    def _deliver(self, msg_type, fields):
        """Sign and send one message. Returns the reply, or None if the Monitoring System did not answer."""
        message = {"adc_id": self.adc_id, "req_id": uuid.uuid4().hex, "type": msg_type}
        message.update(fields)
        try:
            signature = self.app.adc_authentication.make_sign(self.secret, message)
            result = self.app.adc_communication.receive(message, signature)
        except Exception:
            self.need_check = True
            return None
        if not result.ok:
            self.rejected.append((msg_type, result.message))
        return result

    def _login(self):
        if self.token is None:
            login = self.app.access.login("admin_demo", "password")
            if not login.ok:
                print("Could not log in to the Monitoring System:", login.message)
                return False
            self.token = login.data["token"]
        return True

    def show(self):
        """Prints what hospital staff see at the Monitoring System."""
        if not self._login():
            return
        dashboard = self.app.dashboard.view(self.token)
        print("Monitoring System dashboard:")
        if dashboard.ok:
            for adc in dashboard.data["adcs"]:
                print("   ", adc)
        alarms = self.app.alarms.view(self.token)
        print("Monitoring System alarms:")
        if alarms.ok:
            for alarm in alarms.data["alarms"]:
                print("   ", alarm)
        history = self.app.history.search(
            self.token,
            adc_id=self.adc_id,
            event_type="access_attempt"
        )
        print("Monitoring System access history:")
        if history.ok:
            for event in history.data["events"]:
                print("   ", event)
        else:
            print("   ", history.message)
        if len(self.rejected) > 0:
            print("Refused by the Monitoring System:", self.rejected)

    def acknowledge(self, alarm_id):
        if not self._login():
            return
        print(self.app.alarms.acknowledge(alarm_id, self.token).message)