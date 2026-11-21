"""
Runs a demo of the MS.
"""

from app import HospitalMonitoringApp
from monitoring.models import Configuration

def main():
    # creating the system
    app = HospitalMonitoringApp()
    print("MS started")

    # creating a registered ADC
    result = app.store.register_adc("ADC-01")
    print("Storage registration: ", result.message)
    result = app.adc_authentication.register_adc("ADC-01")
    print("Authentication registration:", result.message)

    if not result.ok:
        return

    secret = result.data["secret"]  # for ADC to sign messages


    # creating and logging in a nurse
    result = app.access.add_user("nurse1", "Random PasswordTest123!", "nurse")
    print("User created: ", result.message)
    
    login = app.access.login("nurse1", "Random PasswordTest123!")
    print("Login: ", login.message)

    if not login.ok:
        return

    token = login.data["token"]


    # registering an approved config
    config = Configuration("ADC-01", 1, True, 10, ["Medication 1 at 09:00"])

    result = app.configurations.register(config)
    print("Configuration:", result.message)


    # simulate a signed ADC connection
    connection_check = {"adc_id": "ADC-01", "req_id": "REQ-001", "type": "connection_check"}
    signature = app.adc_authentication.make_sign(secret, connection_check)
    result = app.adc_communication.receive(connection_check, signature)
    print("Connection: ", result.message)


    # simulating a healthy ADC
    health_message = {"adc_id": "ADC-01", "req_id": "REQ-002", "type": "health", "health": "Healthy"}
    signature = app.adc_authentication.make_sign(secret, health_message)
    result = app.adc_communication.receive(health_message, signature)
    print("Health update: ", result.message)


    # simulating below threshold inv
    inventory_message = {"adc_id": "ADC-01", "req_id": "REQ-003", "type": "inventory", "quantity": 8}
    signature = app.adc_authentication.make_sign(secret, inventory_message)
    result = app.adc_communication.receive(inventory_message, signature)
    print("Inventory update: ", result.message)


    # show dashboard
    dash = app.dashboard.view(token)
    print("\nDASHBOARD")

    if dash.ok:
        for adc in dash.data["adcs"]:
            print(adc)
    else:
        print(dash.message)


    # requesting approved config
    req = {"adc_id": "ADC-01", "req_id": "REQ-004", "type": "get_config"}
    signature = app.adc_authentication.make_sign(secret, req)
    result = app.adc_communication.receive(req, signature)
    print("\nConfiguration request:", result.message)

    if result.ok:
        print(result.data)


    # simulating an ADC alarm
    alarm_message = {"adc_id": "ADC-01", "req_id": "REQ-005", "type": "alarm", "alarm_id": "ALM-01", "message": "Medication inventory is low"}
    signature = app.adc_authentication.make_sign(secret, alarm_message)
    result = app.adc_communication.receive(alarm_message, signature)
    print("\nAlarm received: ", result.message)


    # nurse acknowledging alarm
    result = app.alarms.acknowledge("ALM-01", token)
    print("Alarm acknowledgment: ", result.message)


    # display alarms
    result = app.alarms.view(token)
    print("\nALARMS")

    if result.ok:
        for alarm in result.data["alarms"]:
            print(alarm)


    # log out
    result = app.access.logout(token)
    print("\nLogout: ", result.message)

if __name__ == "__main__":
    main()