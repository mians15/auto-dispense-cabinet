
from monitoring.storage import MonitoringStorage
from monitoring.access_control import AccessControl
from monitoring.adc_authentication import ADCAuthentication
from monitoring.configuration_management import ConfigurationManagement
from monitoring.operating_dashboard import OperatorDashboard
from monitoring.requesting_handling import RequestHandler
from monitoring.integration import ADCCommunication

from monitoring.inventory_supervision import InventorySupervision
from monitoring.alarm_management import AlarmManagement
from monitoring.cabinet_health import CabinetHealthMonitoring
from monitoring.historical_data import HistoricalDataManagement
from monitoring.reporting import Reporting


class HospitalMonitoringApp:
    def __init__(self):

        # Shared storage
        self.store = MonitoringStorage()

        # User and ADC authentication
        self.access = AccessControl()
        self.adc_authentication = ADCAuthentication()

        # Configuration management
        self.configurations = ConfigurationManagement(self.store)

        # Request handling
        self.requests = RequestHandler(
            self.store,
            self.configurations,
            self.adc_authentication
        )

        # Operator dashboard
        self.dashboard = OperatorDashboard(
            self.store,
            self.access,
            self.configurations
        )

        # Inventory supervision
        self.inventory = InventorySupervision(
            self.store,
            self.access,
            self.configurations
        )

        # Alarm management
        self.alarms = AlarmManagement(
            self.store,
            self.access
        )

        # Cabinet health monitoring
        self.health = CabinetHealthMonitoring(
            self.store,
            self.access
        )

        # Historical data management
        self.history = HistoricalDataManagement(
            self.store,
            self.access
        )

        # Reporting
        self.reporting = Reporting(
            self.history
        )

        # ADC communication
        self.adc_communication = ADCCommunication(
            self.store,
            self.adc_authentication,
            self.requests
        )
