
"""
Interactive demonstration of the Hospital Monitoring System.

Run from the repository root:
    python3 interactive_demo.py
"""

from uuid import uuid4
from pprint import pprint

from app import HospitalMonitoringApp
from models import Configuration

ADC_ID = "ADC-01"

# Demo credentials
DEMO_PASSWORD = "password"


def show(result):
    print("\n" + ("SUCCESS: " if result.ok else "FAILED: ") + result.message)

    if result.data is not None:
        pprint(result.data, sort_dicts=False)


def ask_int(prompt):
    try:
        return int(input(prompt).strip())
    except ValueError:
        print("Please enter a whole number.")
        return None


def main():
    app = HospitalMonitoringApp()

    print("\n=== Hospital Monitoring System | Interactive Demo ===")

    # --------------------------------------------------
    # INITIAL SETUP
    # --------------------------------------------------

    # Register ADC
    show(app.store.register_adc(ADC_ID))

    # Register ADC authentication
    auth_registration = app.adc_authentication.register_adc(ADC_ID)

    print(
        "ADC authentication registration:",
        auth_registration.message
    )

    if not auth_registration.ok:
        return

    secret = auth_registration.data["secret"]

    # Register approved configuration
    show(
        app.configurations.register(
            Configuration(
                ADC_ID,
                1,
                True,
                10,
                ["Medication 1 at 09:00"]
            )
        )
    )

    # --------------------------------------------------
    # CREATE DEMO USERS
    # --------------------------------------------------

    demo_users = [
        ("admin_demo", "administrator"),
        ("nurse_demo", "nurse"),
        ("pharmacist_demo", "pharmacist"),
        ("tech_demo", "technician")
    ]

    print("\n--- Creating Demo Users ---")

    for demo_username, role in demo_users:

        created = app.access.add_user(
            demo_username,
            DEMO_PASSWORD,
            role
        )

        print(
            "Creating user:",
            demo_username,
            "|",
            created.message
        )

        if not created.ok:
            show(created)

    # --------------------------------------------------
    # TEST LOGIN
    # --------------------------------------------------

    print("\n--- Testing Administrator Login ---")

    test_login = app.access.login(
        "admin_demo",
        DEMO_PASSWORD
    )

    print(
        "TEST LOGIN:",
        test_login.ok,
        test_login.message
    )

    if test_login.ok:
        app.access.logout(test_login.data["token"])
    else:
        print(
            "WARNING: Demo login failed. "
            "Check monitoring/access_control.py."
        )

    # Current logged-in user
    token = None
    username = None

    # --------------------------------------------------
    # SEND AUTHENTICATED ADC MESSAGES
    # --------------------------------------------------

    def send_adc(message_type, **fields):

        message = {
            "adc_id": ADC_ID,
            "req_id": uuid4().hex,
            "type": message_type,
            **fields
        }

        signature = app.adc_authentication.make_sign(
            secret,
            message
        )

        result = app.adc_communication.receive(
            message,
            signature
        )

        show(result)

        return result

    # --------------------------------------------------
    # INITIAL ADC DATA
    # --------------------------------------------------

    send_adc("connection_check")

    send_adc(
        "health",
        health="Healthy"
    )

    send_adc(
        "inventory",
        quantity=8
    )

    # --------------------------------------------------
    # CHECK LOGIN
    # --------------------------------------------------

    def require_login():

        if token is None:
            print("Please log in first (option 1).")
            return False

        return True

    # --------------------------------------------------
    # INTERACTIVE MENU
    # --------------------------------------------------

    while True:

        print("\n" + "=" * 48)

        print("Logged in as:", username or "Nobody")

        print("\n--- MAIN MENU ---")

        print("1. Log in / switch user")
        print("2. View dashboard")
        print("3. Update inventory")
        print("4. Update cabinet health")
        print("5. View inventory records")
        print("6. View cabinet health records")
        print("7. Send alarm")
        print("8. View alarms")
        print("9. Acknowledge alarm")
        print("10. View historical events")
        print("11. Generate report")
        print("12. Disconnect ADC")
        print("13. Reconnect ADC")
        print("0. Exit")

        choice = input("\nSelect an option: ").strip()

        # ----------------------------------------------
        # EXIT
        # ----------------------------------------------

        if choice == "0":

            if token is not None:
                show(app.access.logout(token))

            print("Demo finished.")
            break

        # ----------------------------------------------
        # LOGIN
        # ----------------------------------------------

        elif choice == "1":

            print("\nAvailable demo users:")

            for demo_username, role in demo_users:
                print(f"  {demo_username} ({role})")

            new_username = input(
                "\nUsername: "
            ).strip()

            entered_password = input(
                "Password: "
            ).strip()

            login = app.access.login(
                new_username,
                entered_password
            )

            show(login)

            if login.ok:

                if token is not None:
                    app.access.logout(token)

                token = login.data["token"]
                username = new_username

                print(
                    "\nSuccessfully logged in as:",
                    username
                )

        # ----------------------------------------------
        # DASHBOARD
        # ----------------------------------------------

        elif choice == "2":

            if require_login():

                if app.access.authorize(
                    token,
                    "dashboard:view"
                ):

                    adc = app.store.get_adc(ADC_ID)

                    pprint({
                        "adc_id": adc.adc_id,
                        "connected": adc.connected,
                        "health": (
                            adc.health
                            if adc.connected
                            else "Unavailable"
                        ),
                        "inventory": (
                            adc.inv
                            if adc.connected and adc.inv_current
                            else "Unavailable"
                        )
                    })

                else:
                    print("Access denied.")

        # ----------------------------------------------
        # UPDATE INVENTORY
        # ----------------------------------------------

        elif choice == "3":

            quantity = ask_int(
                "New inventory quantity: "
            )

            if quantity is not None:

                send_adc(
                    "inventory",
                    quantity=quantity
                )

        # ----------------------------------------------
        # UPDATE CABINET HEALTH
        # ----------------------------------------------

        elif choice == "4":

            health = input(
                "Health (Healthy / Fault / Maintenance): "
            ).strip()

            send_adc(
                "health",
                health=health
            )

        # ----------------------------------------------
        # VIEW INVENTORY
        # ----------------------------------------------

        elif choice == "5":

            if require_login():

                show(
                    app.inventory.view(token)
                )

        # ----------------------------------------------
        # VIEW HEALTH
        # ----------------------------------------------

        elif choice == "6":

            if require_login():

                show(
                    app.health.view(token)
                )

        # ----------------------------------------------
        # SEND ALARM
        # ----------------------------------------------

        elif choice == "7":

            alarm_id = input(
                "Alarm ID (e.g., ALM-02): "
            ).strip()

            message = input(
                "Alarm message: "
            ).strip()

            send_adc(
                "alarm",
                alarm_id=alarm_id,
                message=message
            )

        # ----------------------------------------------
        # VIEW ALARMS
        # ----------------------------------------------

        elif choice == "8":

            if require_login():

                show(
                    app.alarms.view(token)
                )

        # ----------------------------------------------
        # ACKNOWLEDGE ALARM
        # ----------------------------------------------

        elif choice == "9":

            if require_login():

                alarm_id = input(
                    "Alarm ID to acknowledge: "
                ).strip()

                show(
                    app.alarms.acknowledge(
                        alarm_id,
                        token
                    )
                )

        # ----------------------------------------------
        # HISTORICAL EVENTS
        # ----------------------------------------------

        elif choice == "10":

            if require_login():

                event_type = input(
                    "Event type filter (Enter for all): "
                ).strip() or None

                show(
                    app.history.search(
                        token,
                        event_type=event_type
                    )
                )

        # ----------------------------------------------
        # GENERATE REPORT
        # ----------------------------------------------

        elif choice == "11":

            if require_login():

                show(
                    app.reporting.generate(token)
                )

        # ----------------------------------------------
        # DISCONNECT ADC
        # ----------------------------------------------

        elif choice == "12":

            send_adc("disconnect")

        # ----------------------------------------------
        # RECONNECT ADC
        # ----------------------------------------------

        elif choice == "13":

            send_adc("connection_check")

        # ----------------------------------------------
        # INVALID MENU OPTION
        # ----------------------------------------------

        else:
            print("Unknown option. Try again.")


if __name__ == "__main__":
    main()
