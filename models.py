"""
Shared data models for the MS.

These classes are for information stored about ADCs, configurations 
(such as medication schedules), and operation results.
"""


class ADC:
    def __init__(self, adc_id, connected=False, health="Unknown", inv=None, inv_current=False):
            
            if not isinstance(adc_id, str) or not adc_id.strip():
                raise ValueError("Invalid ADC ID. ID has to be a non-empty string")

            if type(connected) is not bool:
                raise ValueError("Connected must be True/False") 

            if health not in ["Unknown", "Healthy", "Fault", "Maintenance"]:
                raise ValueError("Invalid health status")
            
            if inv is not None:
                if type(inv) is not int or inv < 0:
                    raise ValueError("Inventory has to be a non-negative integer")

            if type(inv_current) is not bool:
                raise ValueError("Inventory current must be True/False")

            if inv_current and inv is None:
                raise ValueError("Inventory can't be current without a reading")
            
            
            self.adc_id = adc_id
            self.connected = connected
            self.health = health            # healthy, fault, maintenance, or unknown
            self.inv = inv                  # amount in inventory 
            self.inv_current = inv_current  # if its up to date
    

class Configuration:
      def __init__(self, adc_id, version, approved, min_inv, med_sched=None):
            
            if not isinstance(adc_id, str) or not adc_id.strip():
                raise ValueError("Invalid ADC ID. ID has to be a non-empty string")

            if type(version) is not int or version < 1:
                raise ValueError("Version must be a positive integer")

            if type(approved) is not bool:
                raise ValueError("Approved must be True/False")

            if type(min_inv) is not int or min_inv < 0:
                raise ValueError("Minimum inventory must be non-negative integer")


            if med_sched is None:
            # if no medical schedule is given
                med_sched = []              # empty list
            else:
                if not isinstance(med_sched, (list, tuple)):
                    raise ValueError("Medication schedules must be a list or tuple")
                
                med_sched = list(med_sched) # put the schedules in a list

                for schedule in med_sched:
                    if not isinstance(schedule, str) or not schedule.strip():
                        raise ValueError("Invalid medication schedule")
            
            self.adc_id = adc_id
            self.version = version      # if we change the threshold we have multiple versions
            self.approved = approved    # whether the configuration is approved to use
            self.min_inv = min_inv      # minimum inventory threshold
            self.med_sched = med_sched

           
class Result:
    def __init__(self, ok, message, data=None):
        
        if type(ok) is not bool:
            raise ValueError("Result ok must be True/False")

        if not isinstance(message, str):
            raise ValueError("Result message must be a string")

        if data is None:
        # data is for any extra info we might want to communicate
            data = {}
        
        if not isinstance(data, dict):
            raise ValueError("Result data must be a dictionary")
        self.data = data.copy() # copy because I don't want this to be changed if the original data is changed accidentally
        
        self.ok = ok            # to show if the operation worked or not (boolean)
        self.message = message
