"""
main.py - ADC main controller with a small console menu.

"""

import csv
import os
import time
from datetime import datetime

from authenticator import Authenticator
from mode_manager import ModeManager
from fault_detector import FaultDetector
from alarm_manager import AlarmManager
from dispense import Dispenser
from access_log import Access_Log              
from communication import Communication      
from inventory import Inventory
from hardware import Hardware
from monitoring_system import MonitoringSystem

DRAWERS = [1, 2]   # the drawer numbers of the cabinet

USERS = {
    "B1": {"id": "nurse1", "role": "NURSE", "pin": "1234"},
    "B2": {"id": "tech1", "role": "TECH", "pin": "9999"},
}

hw = Hardware(DRAWERS)
monit = MonitoringSystem() # temporary monitor for demo purposes
inventory = Inventory()
comm = Communication(monit)
access_log = Access_Log(comm)
mode_log = []
fault_log = []


alarms = AlarmManager(comm.send_to_communicator)
detector = FaultDetector(DRAWERS, hw)
modes = ModeManager(
    mode_log,
    fault_detector=detector
)   
auth = Authenticator(USERS, access_log, modes, alarms.raise_security_alert)
dispenser = Dispenser(auth, inventory, hw, detector, alarms)

# Stamps time for accurate logging
def stamp():
    return datetime.now().strftime("%H:%M:%S")


def change_mode(event, role=None, fault_class="B"):
    """The only place the mode changes: it tells the Monitoring System and keeps the alarm in step."""
    old = modes.current
    modes.trigger(event, role, fault_class)
    new = modes.current

    if new != old:
        comm.send_to_communicator("MODE", "Mode changed to " + new)

    if new != "FAULT":
        alarms.clear()

def handle_fault(fault):
    """fault = (kind, class, drawer). Switch to FAULT, lock every drawer, sound the alarm, log it."""
    change_mode("fault", None, fault[1])
    for d in DRAWERS:
        hw.lock(d)
        detector.watch_lock_command(d, "LOCKED")
    dispenser.cancel()
    alarms.raise_alarm(fault)
    fault_log.append((stamp(), "FAULT", None, fault[0] + " class " + fault[1] + " drawer " + str(fault[2])))


def problems_to_faults(problems):
    """Turn the results of detector.safety_check() into faults."""
    faults = []
    for kind, drawer in problems:
        if kind == "LOCK_NOT_LOCKED":
            kind = "LOCK_SILENT"
        faults.append((kind, CLASS_OF[kind], drawer))
    return faults


def startup():
    problems = detector.safety_check()
    if len(problems) == 0:
        change_mode("startup_ok")
    else:
        change_mode("startup_bad")
        for fault in problems_to_faults(problems):
            handle_fault(fault)


def enter_maintenance():
    if not auth.is_permitted("enter_maintenance"):
        return "NOT_PERMITTED"
    change_mode("maint", auth.session[1])
    return "OK"

def exit_maintenance():
    if modes.current != "MAINT":
        print("Not in maintenance mode.")
        return

    print("Running safety check...")
    safety_check_passed = modes.run_safety_check()

    if safety_check_passed:
        modes.trigger(
            "exit_ok",
            role=auth.session[1],
            safety_check_passed=True
        )
        print("Safety check passed.")
        print("Exiting maintenance mode.")
    else:
        modes.trigger(
            "exit_bad",
            role=auth.session[1],
            safety_check_passed=False
        )
        print("Safety check failed.")
        print("Maintenance required.")

def tick():
    """One pass of the main loop: runs before every menu prompt, and every second during 'Wait'."""
    dispenser.update()
    for fault in detector.poll():
        handle_fault(fault)
    detector.clear_resolved()
    # a class A fault is over when nothing is active any more and the safety check passes
    if modes.current == "FAULT" and modes.fault_class == "A" and len(detector.active) == 0:
        if len(detector.safety_check()) == 0:
            change_mode("a_cleared")


MESSAGES = {
    "OK": "Done.",
    "UNKNOWN_BADGE": "User not recognized.",
    "WRONG_PIN": "Incorrect ID or PIN.",
    "LOCKED": "Account locked.",
    "REJECTED_MAINT": "Cabinet in maintenance mode.",
    "REJECTED_FAULT": "Cabinet in fault mode.",
    "ALREADY_LOGGED_IN": "Someone is already logged in.",
    "UNLOCKED": "Drawer unlocked.",
    "NOT_PERMITTED": "Not permitted right now.",
    "BUSY": "Another dispense is in progress.",
    "NO_PATIENT": "Select a patient first.",
    "UNAVAILABLE": "Unavailable in this cabinet.",
    "OUT_OF_STOCK": "Out of stock.",
    "INSUFFICIENT": "Insufficient stock.",
    "CHECK_FAILED": "Safety check failed. Cabinet is in fault mode.",
}

MENU = """
 1 Log in            2 Log out           3 Dispense
 4 Enter maintenance 5 Exit maintenance  6 Wait N seconds     
 7 Show logs         8 Open drawer       9 Take a dose      
 10 Close drawer     11 Jam a Lock       12 Kill a sensor   
 13 Repair           0 Quit """


def say(code):
    print(MESSAGES.get(code, code))


def ask(prompt):
    return input(prompt).strip()


def ask_number(prompt):
    text = ask(prompt)
    if text.isdigit():
        return int(text)
    return -1


def show_status():
    if auth.session is None:
        who = "nobody"
    else:
        who = auth.session[0] + " (" + auth.session[1] + ")"
    print("\n" + "=" * 60)
    print("Mode:", modes.current, "  User:", who)
    if alarms.active:
        print("*** " + alarms.message + " ***")
    print("Cabinet:", hw.describe())


def act_on_cabinet(choice):
    d = ask_number("Drawer: ")
    if d not in DRAWERS:
        print("No such drawer.")
    elif choice == "8":
        if not hw.open_drawer(d):
            print("The drawer is locked.")
    elif choice == "9":
        if not hw.take_dose(d):
            print("The drawer is closed.")
    elif choice == "10":
        hw.close_drawer(d)
    elif choice == "11":
        hw.jam_lock(d)
        detector.watch_lock_command(d, "LOCKED")
    else:
        hw.kill_sensor(d)


def show_logs():
    print("Access log:")
    with open(access_log.filename, "r", newline="") as f:
        reader = csv.reader(f)
        for record in reader:
            print("   ", record)
    print("Mode log:")
    for record in mode_log:
        print("   ", record)
    print("Fault log:")
    for record in fault_log:
        print("   ", record)
    print("Inventory log:")
    for record in inventory.records:
        print("   ", record)
    print("Doses left:", inventory.counts)


def main():
   
    startup()
    while True:
        print("Users: badge B1 pin 1234 = nurse, badge B2 pin 9999 = technician")
        print("Drugs: morphine (drawer 1), insulin (drawer 2)")
        tick()
        show_status()
        print(MENU)
        choice = ask("> ")
        if choice == "0":
            break
        elif choice == "1":
            badge = ask("Badge: ")
            pin = ask("PIN: ")
            say(auth.login(badge, pin))
        elif choice == "2":
            auth.logout()
            print("Logged out.")
        elif choice == "3":
            drug = ask("Drug: ")
            patient = ask("Patient ID: ")
            say(dispenser.request(drug, 1, patient))
        elif choice == "4":
            enter_maintenance()
        elif choice == "5":
            exit_maintenance()
        elif choice == "6":
            for i in range(ask_number("Seconds: ")):
                time.sleep(1)
                tick()
        elif choice == "7":
            show_logs()
        elif choice in ("8", "9", "10", "11", "12"):
            act_on_cabinet(choice)
        elif choice == "13":
            hw.repair_all()
            print("Everything repaired.")
        else:
            print("Unknown choice.")


if __name__ == "__main__":
    main()