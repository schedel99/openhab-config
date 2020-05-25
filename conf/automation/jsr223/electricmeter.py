from org.joda.time import DateTime
from org.joda.time.format import DateTimeFormat

from custom.helper import rule, getNow, getHistoricItemEntry, getHistoricItemState, getItemLastUpdate, getItemState, postUpdate, postUpdateIfChanged
from core.triggers import CronTrigger, ItemStateChangeTrigger

def getHistoricReference(log, itemName, valueTime, outdatetTime, messureTime, intervalTime):
    endTime = getItemLastUpdate(itemName)
    endTimestampInMillis = endTime.getMillis()

    nowInMillis = getNow().getMillis()
 
    if endTimestampInMillis < nowInMillis - ( outdatetTime * 1000 ):
        log.info( u"No consumption. Last value is too old." )
        return 0

    minMessuredTimestampInMillis = nowInMillis - ( messureTime * 1000 )

    endValue = getItemState(itemName).doubleValue()

    startTimestampInMillis = endTimestampInMillis
    startValue = 0

    currentTime = DateTime( startTimestampInMillis - 1 )

    itemCount = 0

    while True:
        itemCount = itemCount + 1

        historicEntry = getHistoricItemEntry(itemName, currentTime )

        startValue = historicEntry.getState().doubleValue()

        _millis = historicEntry.getTimestamp().getTime()

        # current item is older then the allowed timeRange
        if _millis < minMessuredTimestampInMillis:
            log.info( u"Consumption time limit exceeded" )
            startTimestampInMillis = startTimestampInMillis - (intervalTime * 1000)
            if _millis > startTimestampInMillis:
                 startTimestampInMillis = _millis
            break
        # 2 items are enough to calculate with
        elif itemCount >= 2:
            log.info( u"Consumption max item count exceeded" )
            startTimestampInMillis = _millis
            break
        else:
            startTimestampInMillis = _millis
            currentTime = DateTime( startTimestampInMillis - 1 )

    durationInSeconds = round(float(endTimestampInMillis - startTimestampInMillis) / 1000.0)
    value = ( (endValue - startValue) / durationInSeconds) * valueTime
    if value < 0:
        value = 0

    if itemName == 'Electricity_Meter':
        display_value = int( round( value * 12 * 1000) )
    else:
        display_value = value

    startTime = DateTime(startTimestampInMillis)
    log.info( u"Consumption {} messured from {} ({}) to {} ({})".format(display_value,startValue,dateTimeFormatter.print(startTime),endValue,dateTimeFormatter.print(endTime)))

    return value
  
@rule("values_em_ht_consumption.py")
class EnergyConsumptionRule:
    def __init__(self):
        self.triggers = [
            #ItemStateChangeTrigger("Electric_Meter_NT"),
            ItemStateChangeTrigger("Electric_Meter_HT")
        ]

    def execute(self, module, input):
        now = getNow()
        zaehlerStandCurrent = getItemState("Electric_Meter_HT").doubleValue()

        # *** Aktueller Verbrauch ***
        value5Min = getHistoricReference( self.log, "Electric_Meter_HT", 300, 360, 900, 300 )
        
        # convert kwh to watt/5min
        # mit 12 multiplizieren da Zählerstand in KW pro Stunde ist
        watt5Min = int( round( value5Min * 12 * 1000 ) )

        postUpdateIfChanged("Electricity_Current_Consumption",watt5Min)

        # *** Tagesverbrauch ***
        zaehlerStandOld = getHistoricItemState("Electric_Meter_HT", now.withTimeAtStartOfDay() ).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electricity_Current_Daily_Consumption",currentConsumption)

        # *** Jahresverbrauch ***
        zaehlerStandOld = getHistoricItemState("Electric_Meter_HT", now.withDate(now.getYear()-1, 12, 31 )).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld

        if postUpdateIfChanged("Electricity_Annual_Consumption", currentConsumption ):
            # Hochrechnung
            zaehlerStandCurrentOneYearBefore = getHistoricItemState("Electric_Meter_HT", now.minusYears(1) ).doubleValue()
            forecastConsumtion = zaehlerStandOld - zaehlerStandCurrentOneYearBefore

            zaehlerStandOldOneYearBefore = getHistoricItemState("Electric_Meter_HT", now.withDate(now.getYear()-2, 12, 31 )).doubleValue()
