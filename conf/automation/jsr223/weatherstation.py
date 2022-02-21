from shared.helper import rule, getMaxItemState, postUpdateIfChanged
from shared.triggers import CronTrigger


@rule("sensor_weatherstation.py")
class UpdateWindRule:
    def __init__(self):
        self.triggers = [
          CronTrigger("0 */5 * * * ?")
        ]

    def execute(self, module, input):
        value = getMaxItemState("WeatherStation_Wind_Gust", ZonedDateTime.now().minusMinutes(15)).doubleValue()
        postUpdateIfChanged("WeatherStation_Wind_Gust_15Min", value)

        value = getMaxItemState("WeatherStation_Wind_Gust", ZonedDateTime.now().minusMinutes(60)).doubleValue()
        postUpdateIfChanged("WeatherStation_Wind_Gust_1h", value)

        value = getMaxItemState("WeatherStation_Wind_Speed", ZonedDateTime.now().minusMinutes(15)).doubleValue()
        postUpdateIfChanged("WeatherStation_Wind_Speed_15Min", value)

        value = getMaxItemState("WeatherStation_Wind_Speed", ZonedDateTime.now().minusMinutes(60)).doubleValue()
        postUpdateIfChanged("WeatherStation_Wind_Speed_1h", value)
