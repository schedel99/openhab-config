<?php
class Environment
{
    public static function getInfluxDBIntervalConfigs()
    {
        return array(
            "WeatherStation_Wind_Gust_15Min" => new IntervalConfig("WeatherStation_Wind_Gust", "interval", "0 */15 * * * ?", 150, "MAX", 900, 900, 99 ),
            "WeatherStation_Wind_Speed_15Min" => new IntervalConfig("WeatherStation_Wind_Speed", "interval", "0 */15 * * * ?", 150, "MAX", 900, 900, 99 ),
        );
    }
    
    public static function getInfluxPersistanceGroups()
    {
        return array( 'gPersistentChart' );
    }

    public static function getMySQLIntervalConfigs()
    {
        return array(
        );
    }
    
    public static function getMySQLPersistanceGroups()
    {
        return array(
            "gPersistance_History"
        );     
    }
}
 
