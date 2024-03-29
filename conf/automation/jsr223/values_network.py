from shared.helper import rule, postUpdateIfChanged
from shared.triggers import ItemStateChangeTrigger, CronTrigger
from shared.actions import Transformation, Exec

from threading import Thread 
from java.time import ZonedDateTime, Duration
from java.time.temporal import ChronoUnit

from org.openhab.core.types import UnDefType

#wget "http://influxdb:8086/query?u=openhab&p=default123&chunked=true&db=openhab_db&epoch=ns&q=DROP+SERIES+FROM+%22pGF_Fritzbox_WanUpstreamCurrRate%22"
#wget "http://influxdb:8086/query?u=openhab&p=default123&chunked=true&db=openhab_db&epoch=ns&q=DROP+SERIES+FROM+%22pGF_Fritzbox_WanDownstreamCurrRate%22"

#wget "http://influxdb:8086/query?u=openhab&p=default123&chunked=true&db=openhab_db&epoch=ns&q=DROP+SERIES+FROM+%22FritzboxWanUpstreamCurrRate%22"
#wget "http://influxdb:8086/query?u=openhab&p=default123&chunked=true&db=openhab_db&epoch=ns&q=DROP+SERIES+FROM+%22FritzboxWanDownstreamCurrRate%22"

#tail -f /dataDisk/var/log/openhab/events.log | grep -P "pGF_Fritzbox_WanTotalBytesReceived|pGF_Fritzbox_WanDownstreamCurrRate"
@rule("values_network.py")
class ValuesNetworkSpeedRule:
    def __init__(self):
        self.triggers = [
            CronTrigger("0 0 * * * ?"),
            ItemStateChangeTrigger("pGF_Speedtest_Rerun")
        ]
        
        self.messureThread = None
        
    def messure(self):        
        try:
            self.log.info(u"speedtest started")
      
            now = ZonedDateTime.now()
            postUpdateIfChanged("pGF_Speedtest_Time","{:02d}:{:02d}".format(now.getHour(),now.getMinute()))
            postUpdateIfChanged("pGF_Speedtest_Location","Aktiv")

            #result = Exec.executeCommandLine("/usr/bin/speedtest -f json --accept-gdpr --accept-license --server-id 40048",100000)
            result = Exec.executeCommandLine(Duration.ofSeconds(100),"/usr/bin/speedtest","-f", "json", "--accept-gdpr", "--accept-license")
            
            self.log.info(u"speedtest done")

            index = result.find("{\"type\":\"result\"")
            if index != -1:
                json = result[index:]

                resultPing = Transformation.transform("JSONPATH", "$.ping.latency", json )
                resultDownBytes = Transformation.transform("JSONPATH", "$.download.bytes", json )
                resultDownTime = Transformation.transform("JSONPATH", "$.download.elapsed", json )
                resultDown = float(resultDownBytes) * 8 / 1024 / 1024 / ( float(resultDownTime) / 1000 )
                #resultDown = Transformation.transform("JSONPATH", "$.download.bandwidth", json )
                resultUpBytes = Transformation.transform("JSONPATH", "$.upload.bytes", json )
                resultUpTime = Transformation.transform("JSONPATH", "$.upload.elapsed", json )
                resultUp = float(resultUpBytes) * 8 / 1024 / 1024 / ( float(resultUpTime) / 1000 )
                #resultUp = Transformation.transform("JSONPATH", "$.upload.bandwidth", json )
                serverName = Transformation.transform("JSONPATH", "$.server.name", json )
                serverLocation = Transformation.transform("JSONPATH", "$.server.location", json )
                serverCountry = Transformation.transform("JSONPATH", "$.server.country", json )
                
                postUpdateIfChanged("pGF_Speedtest_UpstreamRate",resultUp)
                postUpdateIfChanged("pGF_Speedtest_DownstreamRate",resultDown)
                postUpdateIfChanged("pGF_Speedtest_Ping",resultPing)
                postUpdateIfChanged("pGF_Speedtest_Time","{:02d}:{:02d}".format(now.getHour(),now.getMinute()))
                postUpdateIfChanged("pGF_Speedtest_Location","{} ({})".format(serverName,serverLocation))
                
                #125000
                #"download":{
                #    "bandwidth":31775198,
                #    "bytes":409025600,
                #    "elapsed":11700
                #},
                #"upload":{
                #    "bandwidth":31125193,
                #    "bytes":344309374,
                #    "elapsed":10607
                #},
                
                #247,654572929

                #self.log.info("json: {}".format(json)) 
                #self.log.info("ping: {}, down: {}, up: {}".format(resultPing,round(resultDown / 1024 / 1024,2),round(resultUp / 1024 / 1024,2))) 
                #self.log.info("server: {} ({}, {})".format(serverName,serverLocation,serverCountry)) 
            else:
                #postUpdateIfChanged("pGF_Speedtest_UpstreamRate",0)
                #postUpdateIfChanged("pGF_Speedtest_DownstreamRate",0)
                #postUpdateIfChanged("pGF_Speedtest_Ping",0)
                
                postUpdateIfChanged("pGF_Speedtest_Time","{:02d}:{:02d}".format(now.getHour(),now.getMinute()))
                postUpdateIfChanged("pGF_Speedtest_Location","Fehler")

                self.log.error(u"speedtest data error: {}".format(result))
        except Exception, e:
            self.log.error(u"speedtest data exception: {}".format(e))
            
        self.messureThread = None
        postUpdateIfChanged("pGF_Speedtest_Rerun",OFF)

    def execute(self, module, input):
        if 'event' in input and input['event'].getItemName() == "pGF_Speedtest_Rerun":
            if input['event'].getItemState() == OFF:
                return
            
        if self.messureThread == None or not self.messureThread.isAlive():
            self.messureThread = Thread(target = self.messure) 
            self.messureThread.start()
      
@rule("values_network.py")
class ValuesNetworkOutgoingTrafficRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("pGF_Fritzbox_WanTotalBytesSent")
        ]
        self.lastUpdate = -1
                
    def execute(self, module, input):
        #self.log.info(u"{}".format(input))

        now = ZonedDateTime.now()
        
        if self.lastUpdate != -1 and not isinstance(input['event'].getItemState(), UnDefType) and not isinstance(input['event'].getOldItemState(), UnDefType):
            currentValue = input['event'].getItemState().longValue()
            prevValue = input['event'].getOldItemState().longValue()

            # binding is uint (32) 
            # => max value can be 4294967295
            # => is also reseted on dsl reconnection
            if currentValue > prevValue:
                diffValue = ( currentValue - prevValue ) * 8
                diffTime = ChronoUnit.SECONDS.between(self.lastUpdate,now)
                speed = round(diffValue / diffTime)
                postUpdateIfChanged("pGF_Fritzbox_WanUpstreamCurrRate",speed)
            else:
                self.log.info(u"wan traffic overflow - prev: {}, current: {}".format(prevValue,currentValue))

            #self.log.info(u"{} {} {} {}".format(currentValue,prevValue,diffValue,diffTime))
            #else:
            #    self.log.info(u"Outgoing - currentValue: {}".format(currentValue))
            #    self.log.info(u"Outgoing - prevValue: {}".format(prevValue))
            #    self.log.info(u"Outgoing - diffValue: {}".format(diffValue))
            #    self.log.info(u"Outgoing - now: {}".format(now))
            #    self.log.info(u"Outgoing - lastUpdate: {}".format(self.lastUpdate))
            #    self.log.info(u"Outgoing - diffTime: {}".format(diffTime))
            #    self.log.info(u"Outgoing - speed: {}".format(speed))

            #self.log.info(u"Upstream {} MBit".format(speed))
        
        self.lastUpdate = now
      
@rule("values_network.py")
class ValuesNetworkIncommingTrafficRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("pGF_Fritzbox_WanTotalBytesReceived")
        ]
        self.lastUpdate = -1

    def execute(self, module, input):
        #self.log.info(u"{}".format(input))

        now = ZonedDateTime.now()

        if self.lastUpdate != -1 and not isinstance(input['event'].getItemState(), UnDefType) and not isinstance(input['event'].getOldItemState(), UnDefType):
            currentValue = input['event'].getItemState().longValue()
            prevValue = input['event'].getOldItemState().longValue()

            # binding is uint (32) 
            # => max value can be 4294967295
            # => is also reseted on dsl reconnection
            if currentValue > prevValue:
                diffValue = ( currentValue - prevValue ) * 8
                diffTime = ChronoUnit.SECONDS.between(self.lastUpdate,now)
                speed = round(diffValue / diffTime)
                postUpdateIfChanged("pGF_Fritzbox_WanDownstreamCurrRate",speed)
            else:
                self.log.info(u"wan traffic overflow - prev: {}, current: {}".format(prevValue,currentValue))

            #else:
            #    self.log.info(u"Incomming - currentValue: {}".format(currentValue))
            #    self.log.info(u"Incomming - prevValue: {}".format(prevValue))
            #    self.log.info(u"Incomming - diffValue: {}".format(diffValue))
            #    self.log.info(u"Incomming - now: {}".format(now))
            #    self.log.info(u"Incomming - lastUpdate: {}".format(self.lastUpdate))
            #    self.log.info(u"Incomming - diffTime: {}".format(diffTime))
            #    self.log.info(u"Incomming - speed: {}".format(speed))

            #self.log.info(u"Downstream {} MBit".format(speed))
        
        self.lastUpdate = now
