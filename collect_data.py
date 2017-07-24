import utility
import webutil

import matplotlib.pyplot as plt
import numpy as np

import ast
import datetime
from dateutil import parser
from dateutil import tz
import json
import math
import os
import os.path
import re
import sys
import time
import urllib2

import MySQLdb

# This import is file you can't see for obvious reasons.
# If you want the program to work, you need:
# OPENWEATHERMAP_API_KEY
# WUNDERGROUND_API_KEY
# DARK_SKY_API_KEY
# mysql_user_name
# mysql_password
# mysql_host
# mysql_database
from secrets import *

darksky = {}
darksky['southbend,us'] = '41.66394,-86.22028'

yahoo = {}
yahoo['southbend,us'] = 'https://www.yahoo.com/news/weather/united-states/indiana/south-bend-12777829'

accuweather = {}
accuweather['southbend,us'] = 'http://www.accuweather.com/en/us/south-bend-in/46617/month/20075_pc?view=table'

wunderground = {}
wunderground['southbend,us'] = 'IN/South_Bend'

YAHOO_FILTER = 'criteria/yahoo_criteria.txt'
ACCUWEATHER_FILTER = 'criteria/accuweather_criteria.txt'

COLORS = ['r', 'b', 'g', 'c', 'm', 'k']

def execute_query(proc_name, params):
    con = MySQLdb.connect(user=mysql_user_name, passwd=mysql_password,
                                  host=mysql_host, db=mysql_database)
    cursor = con.cursor()
    cursor.callproc(proc_name, params)
    cursor.close()
    con.close()

class WeatherData:
    def __init__(self, currently):
        self.timestamp = currently['time']
        self.time = datetime.datetime.utcfromtimestamp(currently['time'])
        self.temp = currently['temperature']
        if 'precipType' in currently:
            self.precip_type = currently['precipType']
        else:
            self.precip_type = None
        self.is_precip = 0.0 if self.precip_type == None else 1.0
        self.wind = currently['windSpeed']
        self.wind_bearing = currently['windBearing']
        self.humidity = currently['humidity']

    def get_dict(self):
        data = {}
        data['timestamp'] = self.timestamp
        data['temp'] = self.temp
        data['is_precip'] = self.is_precip
        data['precip_type'] = self.precip_type
        data['wind'] = self.wind
        data['wind_bearing'] = self.wind_bearing
        data['humidity'] = self.humidity

        return data

    def insert_sql(self, location, service_name):
        execute_query('usp_WeatherDataInsert', (self.time,
                                                       self.temp,
                                                       self.is_precip,
                                                       self.precip_type,
                                                       self.wind,
                                                       self.wind_bearing,
                                                       self.humidity,
                                                       1,
                                                       service_name))

    def __repr__(self):
        return str(self.get_dict())

class ForecastData:
    def __init__(self, forecasted_time, daily):
        self.forecasted_time = forecasted_time
        self.timestamp = daily['time']
        self.time = datetime.datetime.utcfromtimestamp(daily['time'])
        self.temp_max = int(daily['temperatureMax'])
        self.temp_min = int(daily['temperatureMin'])
        self.temp_avg = (self.temp_max + self.temp_min) / 2.0
        self.wind = daily['windSpeed']
        self.wind_bearing = daily['windBearing']
        self.humidity = daily['humidity']
        self.precip_chance = daily['precipProbability']
        self.precip_type = daily.get('precipType', None)

    def get_dict(self):
        data = {}
        data['forecasted_time'] = self.forecasted_time
        data['timestamp'] = self.timestamp
        data['temp_max'] = self.temp_max
        data['temp_avg'] = self.temp_avg
        data['temp_min'] = self.temp_min
        data['wind'] = self.wind
        data['wind_bearing'] = self.wind_bearing
        data['humidity'] = self.humidity
        data['precip_chance'] = self.precip_chance
        data['precip_type'] = self.precip_type

        return data

    def insert_sql(self, location, service_name):
        dtFcastTime = datetime.datetime.utcfromtimestamp(self.forecasted_time)
        execute_query('usp_WeatherForecastDailyInsert', (dtFcastTime,
                                                            self.time,
                                                            self.temp_max,
                                                            self.temp_min,
                                                            self.precip_chance,
                                                            self.precip_type,
                                                            self.wind,
                                                            self.wind_bearing,
                                                            self.humidity,
                                                            1,
                                                            service_name))

    def __repr__(self):
        return str(self.get_dict())

def format_date(dtime):
    return dtime.strftime('%b-%d %H-%M-%S')

def round_hour(timestamp):
    base = datetime.datetime.utcfromtimestamp(timestamp)
    return datetime.datetime(year=base.year, month=base.month, day=base.day, hour=base.hour)

def round_date(timestamp):
    base = datetime.datetime.utcfromtimestamp(timestamp)
    return datetime.datetime(year=base.year, month=base.month, day=base.day)

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def get_json(url):
    resource = urllib2.urlopen(url)
    page_data = resource.read()
    resource.close()
    data = json.loads(page_data)

    return byteify(data)

def get_timestamp(dt):
    timestamp = (dt - datetime.datetime(1970, 1, 1)).total_seconds()

    return int(timestamp)

def get_accuweather_forecast(url):
    data = webutil.find_data_on_page(url, webutil.read_filter_file(ACCUWEATHER_FILTER))[0]
    print(data)

    now = datetime.datetime.now()
    # Round down the time to the closest day and get the timestamp
    now_timestamp = get_timestamp(datetime.datetime(now.date().year, now.date().month, now.date().day))

    # Time to get our stuff into the right format
    res = {}
    res['currently'] = {}
    res['currently']['time'] = get_timestamp(now)
    res['daily'] = {}
    res['daily']['data'] = []

    for i, day in enumerate(data):
        day_data = {}
        day_data['time'] = now_timestamp + 86400 * i
        day_data['temperatureMax'] = int(day[0])
        day_data['temperatureMin'] = int(day[1])
        day_data['precipProbability'] = 0
        day_data['windSpeed'] = 0
        day_data['windBearing'] = 0
        day_data['humidity'] = 0

        res['daily']['data'].append(day_data)

    return res

def get_yahoo_forecast(url):
    data = webutil.find_data_on_page(url, webutil.read_filter_file(YAHOO_FILTER))[0]
    print(data)

    now = datetime.datetime.now()
    # Round down the time to the closest day and get the timestamp
    now_timestamp = get_timestamp(datetime.datetime(now.date().year, now.date().month, now.date().day))

    # Time to get our stuff into the right format
    res = {}
    res['currently'] = {}
    res['currently']['time'] = get_timestamp(now)
    res['daily'] = {}
    res['daily']['data'] = []

    for i, day in enumerate(data):
        day_data = {}
        day_data['time'] = now_timestamp + 86400 * i # 86400 seconds in a day.
        day_data['temperatureMax'] = int(day[2])
        day_data['temperatureMin'] = int(day[1])
        day_data['precipProbability'] = float(day[0]) / 100.0
        day_data['windSpeed'] = 0
        day_data['windBearing'] = 0
        day_data['humidity'] = 0

        res['daily']['data'].append(day_data)

    return res

def get_openweathermap_forecast(loc):
    data = get_json('http://api.openweathermap.org/data/2.5/forecast/daily?appid={}&q={}'.format(OPENWEATHERMAP_API_KEY, loc))

    now = datetime.datetime.now()
    # Round down the time to the closest day and get the timestamp
    now_timestamp = get_timestamp(datetime.datetime(now.date().year, now.date().month, now.date().day))

    res = {}
    res['currently'] = {}
    res['currently']['time'] = get_timestamp(now)
    res['daily'] = {}
    res['daily']['data'] = []

    for i, day in enumerate(data['list']):
        day_data = {}
        day_data['time'] = day['dt']
        # Because fucking Kelvin
        day_data['temperatureMax'] = (day['temp']['max'] - 273.15) * 1.8 + 32
        day_data['temperatureMin'] = (day['temp']['min'] - 273.15) * 1.8 + 32
        day_data['precipProbability'] = 0.0
        day_data['windSpeed'] = day['speed']
        day_data['windBearing'] = day['deg']
        day_data['humidity'] = day['humidity'] / 100.0

        res['daily']['data'].append(day_data)

    return res

def get_wunderground_forecast(loc):
    loc = wunderground[loc]
    data = get_json('http://api.wunderground.com/api/{}/forecast10day/q/{}.json'.format(WUNDERGROUND_API_KEY,loc))

    now = datetime.datetime.now()
    # Round down the time to the closest day and get the timestamp
    now_timestamp = get_timestamp(datetime.datetime(now.date().year, now.date().month, now.date().day))

    res = {}
    res['currently'] = {}
    res['currently']['time'] = get_timestamp(now)
    res['daily'] = {}
    res['daily']['data'] = []

    for i, day in enumerate(data['forecast']['simpleforecast']['forecastday']):
        day_data = {}

        day_data['time'] = int(day['date']['epoch'])
        day_data['temperatureMax'] = int(day['high']['fahrenheit'])
        day_data['temperatureMin'] = int(day['low']['fahrenheit'])
        day_data['precipProbability'] = day['pop'] / 100.0
        day_data['windSpeed'] = day['avewind']['mph']
        day_data['windBearing'] = day['avewind']['degrees']
        day_data['humidity'] = day['avehumidity']

        res['daily']['data'].append(day_data)

    return res

def get_darksky_forecast(latlon):
    data = get_json('https://api.darksky.net/forecast/{}/{}'.format(DARK_SKY_API_KEY,latlon))

    return data

def convert_timestamp(timestamp, fromtz=tz.tzutc(), totz=tz.tzlocal()):
    base = datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=fromtz)
    dif = get_timestamp(base.replace(tzinfo=None)) - get_timestamp(base.astimezone(totz).replace(tzinfo=None))

    return timestamp - dif

# Currently just handles converting from UTC for dark sky forecasts
def handle_format(forecast, fname):
    if 'darksky' in fname:
        totz = tz.gettz(forecast['timezone'])
        forecast['currently']['time'] = convert_timestamp(forecast['currently']['time'], totz=totz)

        for fcast in forecast['hourly']['data']:
            fcast['time'] = convert_timestamp(fcast['time'], totz=totz)

        for fcast in forecast['daily']['data']:
            fcast['time'] = convert_timestamp(fcast['time'], totz=totz)
    else: # Round all dates and hours for forecasts just in case they happen at weird times
        if 'hourly' in forecast:
            for fcast in forecast['hourly']['data']:
                fcast['time'] = get_timestamp(round_hour(fcast['time']))

        # print(forecast)
        for fcast in forecast['daily']['data']:
            # original = fcast['time']
            fcast['time'] = get_timestamp(round_date(fcast['time']))
            # print('Rounded from {} to {}.'.format(datetime.datetime.utcfromtimestamp(original), datetime.datetime.utcfromtimestamp(fcast['time'])))

    return forecast

def do_aggregatesql(location, service_name, data):
    forecast = ast.literal_eval(data)
    forecast = handle_format(forecast, service_name)

    # Make sure we actually have the right data
    if 'currently' in forecast and 'temperature' in forecast['currently']:
        new_data = WeatherData(forecast['currently'])
        new_data.insert_sql(location, service_name)

    for fcast in forecast['daily']['data']:
        new_forecast = ForecastData(forecast['currently']['time'], fcast)
        # We don't care about forecasts made the day of (or after, hypothetically)
        if new_forecast.forecasted_time < new_forecast.timestamp:
            new_forecast.insert_sql(location, service_name)

def aggregatesql(dir_name, analyze_dir, f_re=None):
    daily_data = {}
    hourly_data = {}
    weather_data = {}

    i = 0
    total_files = utility.count_files(dir_name, f_re=f_re)
    for folder in utility.get_directories(dir_name):
        for fname in utility.get_files(folder, search_re=f_re):
            utility.show_bar(i, total_files, message='Aggregate ({} of {}): '.format(i, total_files))
            i += 1
            # Ignore hidden files like this
            if fname.split('/')[-1].startswith('.'):
                continue

            with open(fname, 'r') as f:
                contents = f.read()

            do_aggregatesql('southbend,us', fname.split('-')[-1].split('.')[0], contents)

    print('')

def monitorsql(locations, dir_name, freq, times=-1):
    i = 0
    while i != times:
        start_time = time.time()
        try:
            for (service, location) in locations.iteritems():
                now = datetime.datetime.now()

                try:
                    os.mkdir(dir_name + str(now.date()) + '/')
                except:
                    pass

                if service == 'darksky':
                    print('Getting data from Dark Sky for {}: {}'.format(location, format_date(now)))
                    forecast = get_darksky_forecast(darksky[location])
                    do_aggregatesql(location, 'darksky', str(forecast))
                elif service == 'yahoo':
                    print('Getting data from Yahoo for {}: {}'.format(location, format_date(now)))
                    forecast = get_yahoo_forecast(yahoo[location])
                    do_aggregatesql(location, 'yahoo', str(forecast))
                elif service == 'accuweather':
                    print('Getting data from Accuweather for {}: {}'.format(location, format_date(now)))
                    forecast = get_accuweather_forecast(accuweather[location])
                    do_aggregatesql(location, 'accuweather', str(forecast))
                elif service == 'wunderground':
                    print('Getting data from Weather Underground for {}: {}'.format(location, format_date(now)))
                    forecast = get_wunderground_forecast(location)
                    do_aggregatesql(location, 'wunderground', str(forecast))
                elif service == 'openweathermap':
                    print('Getting data from OpenWeatherMap for {}: {}'.format(location, format_date(now)))
                    forecast = get_openweathermap_forecast(location)
                    do_aggregatesql(location, 'openweathermap', str(forecast))

        except Exception as e:
            print('-------------------------------')
            print('Failed!')
            print(e)
            print('-------------------------------')
        i += 1
        if i == times:
            break
        time_left = freq - (time.time() - start_time)
        while time_left > 0:
            time_left = freq - (time.time() - start_time)
            time.sleep(1)
            sys.stdout.write('\r{} seconds until data is taken.'.format(time_left))
            sys.stdout.flush()
        print('')

def command_line(args):
    freq = int(args.get('freq', 600))
    times = int(args.get('times', -1))
    dir_name = args.get('dir', './data/')
    city = args.get('city', None)
    latlon = args.get('latlon', None)
    fname = args.get('f', None)

    if city != None:
        city = yahoo[city.lower().replace(' ','')]
    if latlon != None:
        latlon = cities[latlon.lower().replace(' ','')]

    if 'monitorsql' in args or 'monitor' in args:
        if fname == None:
            print('Need a file that contains the list of locations to get data for.')
            return
        else:
            with open(fname, 'r') as f:
                contents = f.read()
            locations = ast.literal_eval(contents)
            monitorsql(locations, dir_name, freq, times=times)
    elif 'aggregatesql' in args:
        analyze_dir = args.get('analyze_dir', './analyze/')
        f_re = args.get('re', None)

        aggregatesql(dir_name, analyze_dir, f_re=f_re)
    elif 'forecast' in args:
        if city == None and latlon == None:
            print('Neither the city nor the zip code were entered, cannot get weather data.')
            return
        else:
            print(get_forecast_data(city, zip_code, latlon))
    elif 'weather' in args:
        if city == None and latlon == None:
            print('Neither the city nor the zip code were entered, cannot get weather data.')
            return
        else:
            print(get_weather_data(city, zip_code))

if __name__ == '__main__':
    arg_synonyms = {}
    arg_synonyms['x'] = 'xvar'
    arg_synonyms['var'] = 'yvar'
    arg_synonyms['y'] = 'yvar'
    arg_synonyms['max_var'] = 'maxvar'
    arg_synonyms['min_var'] = 'minvar'

    command_line(utility.command_line_args(arg_synonyms=arg_synonyms))
