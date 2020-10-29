from org.joda.time import DateTime
from org.joda.time.format import DateTimeFormat

from shared.helper import rule, getNow, getItemState, itemStateOlderThen, itemStateNewerThen, getHistoricItemState, sendCommand, postUpdateIfChanged
from core.triggers import CronTrigger, ItemStateChangeTrigger

from org.eclipse.smarthome.core.types.RefreshType import REFRESH


@rule("solar.py")
class SolarTotalYieldRefreshRule:
    def __init__(self):
        self.triggers = [
          CronTrigger("0 * * * * ?")
        ]
        
    def execute(self, module, input):
        now = getNow()

        if itemStateOlderThen("Dawn_Time", now) and itemStateNewerThen("Dusk_Time", now):
            # triggers solar value update
            sendCommand("Solar_Total_Yield",REFRESH)
            
            sendCommand("Solar_AC_Power",REFRESH)
            
            acPower = getItemState('Solar_AC_Power').intValue()
            dailyConsumption = getItemState("Solar_Daily_Yield").doubleValue()
            
            msg = "{} W, {:.2f} kWh".format(acPower,dailyConsumption)
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
        now = getNow()

        currentTotal = getItemState("Solar_Total_Yield").doubleValue()

        startTotal = getHistoricItemState("Solar_Total_Yield", now.withTimeAtStartOfDay() ).doubleValue()
        postUpdateIfChanged("Solar_Daily_Yield",currentTotal - startTotal)
        
        startTotal = getHistoricItemState("Solar_Total_Yield", now.withDate(now.getYear(), 1, 1 ).withTimeAtStartOfDay()).doubleValue()
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
        now = getNow()

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
        now = getNow()

        currentErtrag = getItemState("Solar_Annual_Yield").doubleValue()
        currentEinspeisung = getItemState("Electric_VZ_Jahreseinspeisung").doubleValue()
        
        postUpdateIfChanged("Solar_Annual_Consumption",currentErtrag - currentEinspeisung)
            
