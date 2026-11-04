class Monitor:
    def __init__(self):
        self.messages = []
        self.online = True

    def send(self, message):
        if not self.online:
            return False

        self.messages.append(message)
        print("\nMONITORING SYSTEM:", message)
        return True