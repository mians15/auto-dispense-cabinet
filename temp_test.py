import time
from authenticator import Authenticator
from mode_manager import ModeManager
from fault_detector import FaultDetector
from alarm_manager import AlarmManager

# 1. Dummy Hardware Stub to simulate Alisha's hardware interface
class MockHardware:
    def __init__(self):
        self.open_drawers = set()
        self.locks = {1: "LOCKED", 2: "LOCKED"}
        self.readings = {1: time.time(), 2: time.time()}

    def is_open(self, d):
        return d in self.open_drawers

    def lock_state(self, d):
        return self.locks.get(d, "LOCKED")

    def last_reading(self, d):
        return self.readings.get(d, time.time())

# 2. Dummy Communication Stub to capture outbox messages
def mock_send(msg_type, data):
    print(f"\n[COMM OUTBOX] Type: {msg_type} | Data: {data}\n")

# 3. Initialize Modules
hw = MockHardware()
logs = []
users = {
    "1111": {"id": "U01", "role": "NURSE", "pin": "1234"},
    "2222": {"id": "U02", "role": "TECH", "pin": "5678"}
}

alarm_mgr = AlarmManager(mock_send)
fault_det = FaultDetector([1, 2], hw)
mode_mgr = ModeManager(logs, alarm_manager=alarm_mgr, fault_detector=fault_det)
auth = Authenticator(users, logs, lambda: mode_mgr.current, alarm_mgr.raise_security_alert)

# 4. Interactive Command Loop
def run_interactive_test():
    print("=== ADC Interactive Test Shell ===")
    print("Commands: login <badge> <pin>, logout, mode, trigger <event>, status, exit")
    
    while True:
        prompt = input(f"\n[Current Mode: {mode_mgr.current}] > ").strip().split()
        if not prompt:
            continue
        
        cmd = prompt[0].lower()
        
        if cmd == "exit":
            break
        elif cmd == "login" and len(prompt) == 3:
            badge, pin = prompt[1], prompt[2]
            res = auth.login(badge, pin)
            print(f"Login Result: {res} | Session: {auth.session}")
        elif cmd == "logout":
            auth.logout()
            print("Logged out.")
        elif cmd == "mode":
            print(f"System Mode: {mode_mgr.current} | Fault Class: {mode_mgr.fault_class}")
        elif cmd == "trigger" and len(prompt) >= 2:
            event = prompt[1]
            role = auth.session[1] if auth.session else "NURSE"
            success = mode_mgr.trigger(event=event, role=role, safety_check_passed=True)
            print(f"Trigger '{event}' success: {success} -> New Mode: {mode_mgr.current}")
        elif cmd == "status":
            print(f"Logs count: {len(logs)}")
            print(f"Last Log: {logs[-1] if logs else 'None'}")
        else:
            print("Unknown or invalid command format.")

if __name__ == "__main__":
    run_interactive_test()