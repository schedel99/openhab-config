from org.joda.time import DateTime
from org.joda.time.format import DateTimeFormat

from custom.helper import rule, getNow, itemStateOlderThen, itemStateNewerThen, sendCommand
from core.triggers import CronTrigger

from org.eclipse.smarthome.core.types.RefreshType import REFRESH


@rule("solar_refresh.py")
class EnergyTotalYieldRefreshRule:
    def __init__(self):
        self.triggers = [
          CronTrigger("0 * * * * ?")
        ]
        
    def execute(self, module, input):
        now = getNow()

        if itemStateOlderThen("Dawn_Time", now) and itemStateNewerThen("Dusk_Time", now):
            # triggers solar value update
            sendCommand("Solar_Total_Yield",REFRESH)
            
