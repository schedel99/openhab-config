from java.time import ZonedDateTime, Instant, ZoneId
from java.time.format import DateTimeFormatter
 
from shared.helper import rule, getHistoricItemEntry, getHistoricItemState, getItemLastUpdate, getItemState, postUpdate, postUpdateIfChanged, itemLastUpdateOlderThen
from shared.triggers import CronTrigger, ItemStateChangeTrigger

dateTimeFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSS")

def getHistoricReference(log, itemName, valueTime, outdatetTime, messureTime, intervalTime):
    endTime = getItemLastUpdate(itemName)
    endTimestampInMillis = endTime.toInstant().toEpochMilli()

    nowInMillis = ZonedDateTime.now().toInstant().toEpochMilli()
 
    if endTimestampInMillis < nowInMillis - ( outdatetTime * 1000 ):
        log.info( u"No consumption. Last value is too old." )
        return 0

    minMessuredTimestampInMillis = nowInMillis - ( messureTime * 1000 )

    endValue = getItemState(itemName).doubleValue()

    startTimestampInMillis = endTimestampInMillis
    startValue = 0

    currentTime = ZonedDateTime.ofInstant(Instant.ofEpochMilli(startTimestampInMillis - 1), ZoneId.systemDefault())

    itemCount = 0

    while True:
        itemCount = itemCount + 1

        historicEntry = getHistoricItemEntry(itemName, currentTime )

        startValue = historicEntry.getState().doubleValue()

        _millis = historicEntry.getTimestamp().toInstant().toEpochMilli()

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
            currentTime = ZonedDateTime.ofInstant(Instant.ofEpochMilli(startTimestampInMillis - 1), ZoneId.systemDefault())

    durationInSeconds = round(float(endTimestampInMillis - startTimestampInMillis) / 1000.0)
    value = ( (endValue - startValue) / durationInSeconds) * valueTime
    if value < 0:
        value = 0

    if itemName == 'Electricity_Meter':
        display_value = int( round( value * 12 * 1000) )
    else:
        display_value = value

    startTime = ZonedDateTime.ofInstant(Instant.ofEpochMilli(startTimestampInMillis), ZoneId.systemDefault())

    log.info( u"Consumption {} messured from {} ({}) to {} ({})".format(display_value,startValue,dateTimeFormatter.format(startTime),endValue,dateTimeFormatter.format(endTime)))

    return value

@rule("values_consumption.py")
class EnergyVZSupply5MinRule:
    def __init__(self):
        self.triggers = [CronTrigger("15 */5 * * * ?")]

    def execute(self, module, input):
        # *** Aktueller Verbrauch ***
        value5Min = getHistoricReference( self.log, "Electric_Meter_VZ_Einspeisung", 300, 360, 900, 300 )
        
        # convert kwh to watt/5min
        # mit 12 multiplizieren da Zählerstand in KW pro Stunde ist
        watt5Min = int( round( value5Min * 12 * 1000 ) )

        postUpdateIfChanged("Electric_VZ_Aktuelle_Einspeisung",watt5Min)
        
        if itemLastUpdateOlderThen("Electric_Meter_VZ_Einspeisung", ZonedDateTime.now().minusMinutes(60)):
            self.log.error("Electric meter supply values not updated")

@rule("electricmeter.py")
class EnergyVZSupplyRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("Electric_Meter_VZ_Einspeisung"),
            CronTrigger("1 0 0 * * ?")
        ]

    def execute(self, module, input):
      
        now = ZonedDateTime.now()
        zaehlerStandCurrent = getItemState("Electric_Meter_VZ_Einspeisung").doubleValue()

        # *** Tagesverbrauch ***
        
        zaehlerStandOld = getHistoricItemState("Electric_Meter_VZ_Einspeisung", now.toLocalDate().atStartOfDay(now.getZone())).doubleValue()
        currentSupply = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electric_VZ_Tageseinspeisung",currentSupply)

        # *** Jahresverbrauch ***
        refDate = now.withYear(now.getYear()).withMonth(1).withDayOfMonth(1)
        zaehlerStandOld = getHistoricItemState("Electric_Meter_VZ_Einspeisung", refDate.toLocalDate().atStartOfDay(now.getZone())).doubleValue()
        currentSupply = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electric_VZ_Jahreseinspeisung", currentSupply )

@rule("electricmeter.py")
class EnergyVZMessageRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("Electric_VZ_Tagesverbrauch"),
            ItemStateChangeTrigger("Electric_VZ_Tageseinspeisung")
        ]

    def execute(self, module, input):
        currentConsumption = getItemState("Electric_VZ_Tagesverbrauch").doubleValue()
        currentSupply = getItemState("Electric_VZ_Tageseinspeisung").doubleValue()
        
        msg = u"{:.2f} kWh, {:.2f} kWh".format(currentConsumption,currentSupply)
        postUpdateIfChanged("Electric_VZ_Message",msg)
        
        
        
        
        
        
        
        
        
        
        
        
# **** VZ Consumption ****
@rule("values_consumption.py")
class EnergyVZConsumption5MinRule:
    def __init__(self):
        self.triggers = [CronTrigger("15 */5 * * * ?")]

    def execute(self, module, input):
        # *** Aktueller Verbrauch ***
        value5Min = getHistoricReference( self.log, "Electric_Meter_VZ_Verbrauch", 300, 360, 900, 300 )
        
        # convert kwh to watt/5min
        # mit 12 multiplizieren da Zählerstand in KW pro Stunde ist
        watt5Min = int( round( value5Min * 12 * 1000 ) )

        postUpdateIfChanged("Electric_VZ_Aktueller_Verbrauch",watt5Min)

        if itemLastUpdateOlderThen("Electric_Meter_VZ_Verbrauch", ZonedDateTime.now().minusMinutes(60)):
            self.log.error("Electric meter consumption values not updated")

@rule("electricmeter.py")
class EnergyVZConsumptionRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("Electric_Meter_VZ_Verbrauch"),
            CronTrigger("1 0 0 * * ?")
        ]

    def execute(self, module, input):
      
        now = ZonedDateTime.now()
        zaehlerStandCurrent = getItemState("Electric_Meter_VZ_Verbrauch").doubleValue()

        # *** Tagesverbrauch ***
        zaehlerStandOld = getHistoricItemState("Electric_Meter_VZ_Verbrauch", now.toLocalDate().atStartOfDay(now.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld
        postUpdateIfChanged("Electric_VZ_Tagesverbrauch",currentConsumption)

        # *** Wochenverbrauch ***
        ref = now.toLocalDate()
        ref = ref.minusDays(ref.getDayOfWeek().getValue() - 1)
        zaehlerStandOld = getHistoricItemState("Electric_Meter_VZ_Verbrauch", ref.atStartOfDay(now.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld
        postUpdateIfChanged("Electric_VZ_Wochenverbrauch",currentConsumption)

        # *** Monatsverbrauch ***
        zaehlerStandOld = getHistoricItemState("Electric_Meter_VZ_Verbrauch", now.toLocalDate().withDayOfMonth(1).atStartOfDay(now.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld
        postUpdateIfChanged("Electric_VZ_Monatsverbrauch",currentConsumption)

        # *** Jahresverbrauch ***
        refDay = now.withYear(now.getYear()).withMonth(1).withDayOfMonth(1)
        zaehlerStandOld = getHistoricItemState("Electric_Meter_VZ_Verbrauch", refDay.toLocalDate().atStartOfDay(refDay.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electric_VZ_Jahresverbrauch", currentConsumption )
        
        
        
         
        
        
        
        
        
        
        
        
        
# **** HZ Tag Consumption ****
@rule("values_consumption.py")
class EnergyHZDayConsumption5MinRule:
    def __init__(self):
        self.triggers = [CronTrigger("15 */5 * * * ?")]

    def execute(self, module, input):
        # *** Aktueller Verbrauch ***
        value5Min = getHistoricReference( self.log, "Electric_Meter_HZ_Tag", 300, 360, 900, 300 )
        
        # convert kwh to watt/5min
        # mit 12 multiplizieren da Zählerstand in KW pro Stunde ist
        watt5Min = int( round( value5Min * 12 * 1000 ) )

        postUpdateIfChanged("Electric_HZ_Tag_Aktueller_Verbrauch",watt5Min)

        if itemLastUpdateOlderThen("Electric_Meter_HZ_Tag", ZonedDateTime.now().minusMinutes(60)):
            self.log.error("Electric meter HZ day consumption values not updated")

@rule("electricmeter.py")
class EnergyHZDayConsumptionRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("Electric_Meter_HZ_Tag"),
            CronTrigger("1 0 0 * * ?")
        ]

    def execute(self, module, input):
      
        now = ZonedDateTime.now()
        zaehlerStandCurrent = getItemState("Electric_Meter_HZ_Tag").doubleValue()

        # *** Tagesverbrauch ***
        zaehlerStandOld = getHistoricItemState("Electric_Meter_HZ_Tag", now.toLocalDate().atStartOfDay(now.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electric_HZ_Tag_Tagesverbrauch",currentConsumption)

        # *** Wochenverbrauch ***
        ref = now.toLocalDate()
        ref = ref.minusDays(ref.getDayOfWeek().getValue() - 1)
        zaehlerStandOld = getHistoricItemState("Electric_Meter_HZ_Tag", ref.atStartOfDay(now.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electric_HZ_Tag_Wochenverbrauch",currentConsumption)

        # *** Monatsverbrauch ***
        zaehlerStandOld = getHistoricItemState("Electric_Meter_HZ_Tag", now.toLocalDate().withDayOfMonth(1).atStartOfDay(now.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electric_HZ_Tag_Monatsverbrauch",currentConsumption)

        # *** Jahresverbrauch ***
        refDay = now.withYear(now.getYear()).withMonth(1).withDayOfMonth(1)
        zaehlerStandOld = getHistoricItemState("Electric_Meter_HZ_Tag", refDay.toLocalDate().atStartOfDay(refDay.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electric_HZ_Tag_Jahresverbrauch", currentConsumption )






# **** HZ Night Consumption ****
@rule("values_consumption.py")
class EnergyHZNightConsumption5MinRule:
    def __init__(self):
        self.triggers = [CronTrigger("15 */5 * * * ?")]

    def execute(self, module, input):
        # *** Aktueller Verbrauch ***
        value5Min = getHistoricReference( self.log, "Electric_Meter_HZ_Nacht", 300, 360, 900, 300 )
        
        # convert kwh to watt/5min
        # mit 12 multiplizieren da Zählerstand in KW pro Stunde ist
        watt5Min = int( round( value5Min * 12 * 1000 ) )

        postUpdateIfChanged("Electric_HZ_Nacht_Aktueller_Verbrauch",watt5Min)

        if itemLastUpdateOlderThen("Electric_Meter_HZ_Nacht", ZonedDateTime.now().minusMinutes(60)):
            self.log.error("Electric meter HZ night consumption values not updated")

@rule("electricmeter.py")
class EnergyHZNightConsumptionRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("Electric_Meter_HZ_Nacht"),
            CronTrigger("1 0 0 * * ?")
        ]

    def execute(self, module, input):
      
        now = ZonedDateTime.now()
        zaehlerStandCurrent = getItemState("Electric_Meter_HZ_Nacht").doubleValue()

        # *** Tagesverbrauch ***
        zaehlerStandOld = getHistoricItemState("Electric_Meter_HZ_Nacht", now.toLocalDate().atStartOfDay(now.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electric_HZ_Nacht_Tagesverbrauch",currentConsumption)

        # *** Wochenverbrauch ***
        ref = now.toLocalDate()
        ref = ref.minusDays(ref.getDayOfWeek().getValue() - 1)
        zaehlerStandOld = getHistoricItemState("Electric_Meter_HZ_Nacht", ref.atStartOfDay(now.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electric_HZ_Nacht_Wochenverbrauch",currentConsumption)

        # *** Monatsverbrauch ***
        zaehlerStandOld = getHistoricItemState("Electric_Meter_HZ_Nacht", now.toLocalDate().withDayOfMonth(1).atStartOfDay(now.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electric_HZ_Nacht_Monatsverbrauch",currentConsumption)

        # *** Jahresverbrauch ***
        refDay = now.withYear(now.getYear()).withMonth(1).withDayOfMonth(1)
        zaehlerStandOld = getHistoricItemState("Electric_Meter_HZ_Nacht", refDay.toLocalDate().atStartOfDay(refDay.getZone())).doubleValue()
        currentConsumption = zaehlerStandCurrent - zaehlerStandOld

        postUpdateIfChanged("Electric_HZ_Nacht_Jahresverbrauch", currentConsumption )
        
# *** SUMMERIZE ***
@rule("values_consumption.py")
class EnergyHZConsumption5MinRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("Electric_HZ_Tag_Aktueller_Verbrauch"),
            ItemStateChangeTrigger("Electric_HZ_Nacht_Aktueller_Verbrauch"),
        ]

    def execute(self, module, input):
        tag = getItemState("Electric_HZ_Tag_Aktueller_Verbrauch").intValue()
        nacht = getItemState("Electric_HZ_Nacht_Aktueller_Verbrauch").intValue()
        postUpdateIfChanged("Electric_HZ_Aktueller_Verbrauch",tag+nacht)

@rule("values_consumption.py")
class EnergyHZConsumptionRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("Electric_HZ_Tag_Jahresverbrauch"),
            ItemStateChangeTrigger("Electric_HZ_Nacht_Jahresverbrauch"),
        ]

    def execute(self, module, input):
        tag = getItemState("Electric_HZ_Tag_Tagesverbrauch").doubleValue()
        nacht = getItemState("Electric_HZ_Nacht_Tagesverbrauch").doubleValue()
        postUpdateIfChanged("Electric_HZ_Tagesverbrauch",tag+nacht)

        tag = getItemState("Electric_HZ_Tag_Wochenverbrauch").doubleValue()
        nacht = getItemState("Electric_HZ_Nacht_Wochenverbrauch").doubleValue()
        postUpdateIfChanged("Electric_HZ_Wochenverbrauch",tag+nacht)

        tag = getItemState("Electric_HZ_Tag_Monatsverbrauch").doubleValue()
        nacht = getItemState("Electric_HZ_Nacht_Monatsverbrauch").doubleValue()
        postUpdateIfChanged("Electric_HZ_Monatsverbrauch",tag+nacht)

        tag = getItemState("Electric_HZ_Tag_Jahresverbrauch").doubleValue()
        nacht = getItemState("Electric_HZ_Nacht_Jahresverbrauch").doubleValue()
        postUpdateIfChanged("Electric_HZ_Jahresverbrauch",tag+nacht)
        
        
        
        
        
        
        
        
