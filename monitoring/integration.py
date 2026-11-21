"""
Temporary simulation of ADC communication and Alarm Management.
To be replaced with Maarvi's code after :)
Used to test modules written by Mira
This module is written by ChatGPT
"""

from models import Result

class ADCCommunication:
    def __init__(self, store, adc_authentication, request_handler):
        self.__store = store
        self.__authentication = adc_authentication
        self.__requests = request_handler

    def receive(self, message, signature):
        # RequestHandler verifies requests itself. Do not verify them twice.
        if isinstance(message, dict) and message.get('type') in ('get_config', 'get_status'):
            return self.__requests.handle(message, signature)

        authentication = self.__authentication.verification(message, signature)
        if not authentication.ok:
            self.__store.log('authentication_failed', authentication.message)
            return authentication

        adc_id = authentication.data['adc_id']
        if self.__store.get_adc(adc_id) is None:
            return Result(False, 'Unknown ADC')

        message_type = message.get('type')
        if message_type == 'connection_check':
            return self.__store.update_adc(adc_id, connected=True)
        elif message_type == 'disconnect':
            result = self.__store.update_adc(adc_id, connected=False, inv_current=False)
            if result.ok:
                self.__store.log('communication_loss', adc_id)
            return result
        elif message_type == 'health':
            health = message.get('health')
            if health not in ('Healthy', 'Fault', 'Maintenance'):
                return Result(False, 'Invalid health value')
            return self.__store.update_adc(adc_id, connected=True, health=health)
        elif message_type == 'inventory':
            quantity = message.get('quantity')
            if type(quantity) is not int or quantity < 0:
                self.__store.update_adc(adc_id, inv_current=False)
                return Result(False, 'Invalid inventory quantity')
            return self.__store.update_adc(adc_id, connected=True, inv=quantity, inv_current=True)
        elif message_type == 'alarm':
            result = self.__store.save_alarm(message.get('alarm_id'), adc_id, message.get('message'))
            if result.ok:
                self.__store.log('alarm_received', message['alarm_id'])
            return result
        elif message_type == 'access_log':
            self.__store.log('access_attempt',
                             f"{adc_id}: user {message.get('badge')} {message.get('result')} at {message.get('time')}")
            return Result(True, 'Access record saved')
        return Result(False, 'Unsupported message type')


class AlarmManagement:
    def __init__(self, store, access):
        self.__store = store
        self.__access = access

    def view(self, token):
        if not self.__access.authorize(token, 'alarms:view'):
            return Result(False, 'Access denied')
        return Result(True, 'Alarm records', {'alarms': self.__store.list_alarms()})

    def acknowledge(self, alarm_id, token):
        if not self.__access.authorize(token, 'alarms:acknowledge'):
            return Result(False, 'Access denied')
        alarm = self.__store.get_alarm(alarm_id)
        if alarm is None:
            return Result(False, 'Unknown alarm')
        if alarm['state'] != 'Active':
            return Result(False, 'Alarm is not Active')
        username = self.__access.get_username(token)
        result = self.__store.update_alarm(alarm_id, 'Acknowledged', username)
        if result.ok:
            self.__store.log('alarm_acknowledged', alarm_id + ' by ' + username)
        return result

    def clear(self, alarm_id):
        alarm = self.__store.get_alarm(alarm_id)
        if alarm is None:
            return Result(False, 'Unknown alarm')
        result = self.__store.update_alarm(alarm_id, 'Resolved')
        if result.ok:
            self.__store.log('alarm_resolved', alarm_id)
        return result
