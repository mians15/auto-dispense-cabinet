import csv
import os

class Access_Log:
    def __init__(self, communicator, filename="Access_Log.csv"):
        self.filename = filename
        self.comm = communicator

        # Check if the file does not exist or is empty
        if not os.path.exists(self.filename) or os.path.getsize(self.filename) == 0:
            # Write column headers
            with open(self.filename, "w", newline="") as f:
                csv.writer(f).writerow(["Badge Number", "Result", "Time"])

    
    def __update(self, badge, result, time):
        # append only accepted
        with open(self.filename, "a", newline="") as f:
            csv.writer(f).writerow([badge, result, time])

        # send new update to communicator so it can send it to monitoring system
        self.comm.send_to_communicator("Access Log", f"Badge:{badge}, Login Attempt Result: {result} at {time}")

    def update(self, badge, result, time):
        self.__update(badge, result, time)


    