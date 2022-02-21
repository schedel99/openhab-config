from java.time import ZonedDateTime

from shared.helper import rule, getItemState, itemStateOlderThen, itemStateNewerThen, getHistoricItemState, sendCommand, postUpdateIfChanged, itemLastUpdateOlderThen, getItemLastUpdate
from shared.triggers import CronTrigger, ItemStateChangeTrigger

from org.openhab.core.types.RefreshType import REFRESH

@rule("solar.py")
class SolarTotalYieldRefreshRule:
    def __init__(self):
        self.triggers = [
          CronTrigger("0 * * * * ?")
        ]
        
    def execute(self, module, input):
        now = ZonedDateTime.now()

        if itemStateOlderThen("Dawn_Time", now) and itemStateNewerThen("Dusk_Time", now):
            # triggers solar value update
            sendCommand("Solar_Total_Yield",REFRESH)
            
            sendCommand("Solar_AC_Power",REFRESH)
            
            acPower = getItemState('Solar_AC_Power').intValue()
            dailyConsumption = getItemState("Solar_Daily_Yield").doubleValue()
            
            msg = "{} W, {:.2f} kWh".format(acPower,dailyConsumption)
            
            if itemLastUpdateOlderThen("Solar_Total_Yield", now.minusMinutes(15)) and itemStateOlderThen("Dawn_Time", now.minusMinutes(60)):
                self.log.error("Solar values not updated")
            
        else:
            msg = "Inaktiv"
            
        postUpdateIfChanged("Solar_Message",msg)

@rule("solar.py")
class SolarDailyAnnualYieldRule:
    def __init__(self):
        self.triggers = [
          ItemStateChangeTrigger("Solar_Total_Yield"),
          CronTrigger("1 0 0 * * ?")
        ]
        
    def execute(self, module, input):
        now = ZonedDateTime.now()

        currentTotal = getItemState("Solar_Total_Yield").doubleValue()

        startTotal = getHistoricItemState("Solar_Total_Yield", now.toLocalDate().atStartOfDay(now.getZone())).doubleValue()
        postUpdateIfChanged("Solar_Daily_Yield",currentTotal - startTotal)
        
        refDay = now.withYear(now.getYear()).withMonth(1).withDayOfMonth(1)
        startTotal = getHistoricItemState("Solar_Total_Yield", refDay.toLocalDate().atStartOfDay(refDay.getZone())).doubleValue()
        postUpdateIfChanged("Solar_Annual_Yield",currentTotal - startTotal)
        
            
@rule("solar.py")
class SolarDailyYieldRule:
    def __init__(self):
        self.triggers = [
          ItemStateChangeTrigger("Solar_Daily_Yield"),
          ItemStateChangeTrigger("Electric_VZ_Tageseinspeisung"),
          CronTrigger("1 0 0 * * ?")
        ]
        
    def execute(self, module, input):
        now = ZonedDateTime.now()

        currentErtrag = getItemState("Solar_Daily_Yield").doubleValue()
        currentEinspeisung = getItemState("Electric_VZ_Tageseinspeisung").doubleValue()
        
        postUpdateIfChanged("Solar_Daily_Consumption",currentErtrag - currentEinspeisung)
            
@rule("solar.py")
class SolarAnnualYieldRule:
    def __init__(self):
        self.triggers = [
          ItemStateChangeTrigger("Solar_Annual_Yield"),
          ItemStateChangeTrigger("Electric_VZ_Jahreseinspeisung"),
          CronTrigger("1 0 0 * * ?")
        ]
        
    def execute(self, module, input):
        now = ZonedDateTime.now()

        currentErtrag = getItemState("Solar_Annual_Yield").doubleValue()
        currentEinspeisung = getItemState("Electric_VZ_Jahreseinspeisung").doubleValue()
        
        postUpdateIfChanged("Solar_Annual_Consumption",currentErtrag - currentEinspeisung)
            
