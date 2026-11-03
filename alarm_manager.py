""" Alarm manager module for the ADC"""

import time

DESCRIPTION = {
    "DRAWER_OPEN": "Drawer open too long",
    "NO_REMOVAL":  "No removal detected",
    "LOCK_SILENT": "Lock not responding",
    "SENSOR_DEAD": "Sensor not reporting",
    "SOFTWARE":    "Software failure",
}

class AlarmManager:
    def __init__(self, send):
        self.send = send             # send(message_type, data) from the communication module
        self.active = False
        self.message = ""            # text the screen should show while the alarm is on

    def raise_alarm(self, fault):
        kind, fault_class, drawer = fault
        self.active = True
        self.message = "FAULT: " + DESCRIPTION[kind]
        if drawer is not None:
            self.message += f" (drawer {drawer})"
        if fault_class == "B":
            self.message += " - Maintenance required"                
        data = {"kind": kind, "class": fault_class, "drawer": drawer, "time": time.time()}
        self.send("ALARM", data)                                    
        if fault_class == "B":
            self.send("MAINTENANCE_REQUEST", data)                 

    def raise_security_alert(self, user_id):                            
        self.send("SECURITY_ALERT", {"user_id": user_id, "time": time.time()})

    def raise_stock_alert(self, drawer, drug, count, kind):
        self.send(
            "STOCK_ALERT",
            {
                "drawer": drawer,
                "drug": drug,
                "count": count,
                "type": kind,
                "time": time.time()
            }
        )

    def clear(self):
        """Reset alarm state when leaving FAULT mode."""
        self.active = False
        self.message = ""