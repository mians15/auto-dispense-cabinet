"Simulated Monitoring System for testing of ADC Communicator"

class MonitoringSystem:
    def __init__(self):
        self.online = True
        # received messages are just stored here for testing
        self.received = []

    def send(self, message):
        if not self.online:
            return False

        self.received.append(message)
        print("\nMONITORING SYSTEM:", message)
        # sending acknowledgment to ADC communicator
        return True