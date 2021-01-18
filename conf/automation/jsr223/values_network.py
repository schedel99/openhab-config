from shared.helper import rule, getNow, itemLastUpdateOlderThen, sendNotificationToAllAdmins, getItemState, postUpdateIfChanged
from core.triggers import CronTrigger, ItemStateChangeTrigger

@rule("values_network.py")
class ValuesNetworkOutgoingTrafficRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("FritzboxWanTotalBytesSent")
        ]
        self.lastUpdate = -1

    def execute(self, module, input):
        #self.log.info(u"{}".format(input))

        now = getNow().getMillis()

        if self.lastUpdate != -1:
            currentValue = input['event'].getItemState().longValue()
            prevValue = input['event'].getOldItemState().longValue()

            # binding is uint (32) 
            # => max value can be 4294967295
            # => is also reseted on dsl reconnection
            if currentValue > prevValue:
                diffValue = ( currentValue - prevValue ) * 8
                diffTime = ( now - self.lastUpdate ) / 1000.0
                speed = round(diffValue / diffTime)
                postUpdateIfChanged("FritzboxWanUpstreamCurrRate",speed)
            else:
                self.log.info(u"wan traffic overflow - prev: {}, current: {}".format(prevValue,currentValue))
        
        self.lastUpdate = now
      
@rule("values_network.py")
class ValuesNetworkIncommingTrafficRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("FritzboxWanTotalBytesReceived")
        ]
        self.lastUpdate = -1

    def execute(self, module, input):
        #self.log.info(u"{}".format(input))

        now = getNow().getMillis()

        if self.lastUpdate != -1:
            currentValue = input['event'].getItemState().longValue()
            prevValue = input['event'].getOldItemState().longValue()

            # binding is uint (32) 
            # => max value can be 4294967295
            # => is also reseted on dsl reconnection
            if currentValue > prevValue:
                diffValue = ( currentValue - prevValue ) * 8
                diffTime = ( now - self.lastUpdate ) / 1000.0
                speed = round(diffValue / diffTime)
                postUpdateIfChanged("FritzboxWanDownstreamCurrRate",speed)
            else:
                self.log.info(u"wan traffic overflow - prev: {}, current: {}".format(prevValue,currentValue))

            #self.log.info(u"Downstream {} MBit".format(speed))
        
        self.lastUpdate = now
