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

import mysql.connector

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

con = mysql.connector.connect(user=mysql_user_name, password=mysql_password,
                              host=mysql_host, database=mysql_database)
cursor = con.cursor()

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
        cursor.callproc('main.usp_WeatherDataInsert', (location, service_name, self.time, self.timestamp, 
                                                       self.temp, self.is_precip,
                                                       self.wind, self.precip_type,
                                                       self.wind_bearing, self.humidity))
        con.commit()

    def __repr__(self):
        return str(self.get_dict())

class HourlyForecastData:
    def __init__(self, forecasted_time, hourly):
        self.forecasted_time = forecasted_time
        self.timestamp = hourly['time']
        self.time = datetime.datetime.utcfromtimestamp(hourly['time'])
        self.temp = hourly['temperature']
        self.precip_chance = hourly['precipProbability']
        self.precip_type = hourly.get('precipType', None)
        self.wind = hourly['windSpeed']
        self.wind_bearing = hourly['windBearing']
        self.humidity = hourly['humidity']

    def get_dict(self):
        data = {}
        data['forecasted_time'] = self.forecasted_time
        data['timestamp'] = self.timestamp
        data['temp'] = self.temp
        data['wind'] = self.wind
        data['wind_bearing'] = self.wind_bearing
        data['humidity'] = self.humidity
        data['precip_chance'] = self.precip_chance
        data['precip_type'] = self.precip_type

        return data
        
    def insert_sql(self, location, service_name):
        dtFcastTime = datetime.datetime.utcfromtimestamp(self.forecasted_time)
        cursor.callproc('main.usp_WeatherForecastHourlyInsert', (location, service_name, dtFcast, self.forecasted_time, 
                                                                 self.time, self.timestamp,
                                                                 self.temp, self.wind,
                                                                 self.wind_bearing, self.humidity,
                                                                 self.precip_chance, self.precip_type))
        con.commit()

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
        dtFcastTime = datetime.datetime.utcfromtimestamp(data['forecasted_time'])
        cursor.callproc('main.usp_WeatherForecastDailyInsert', (location, service_name, dtFcastTime, self.forecasted_time,
                                                                self.time, self.timestamp,
                                                                self.temp_max, self.temp_avg,
                                                                self.temp_min, self.wind,
                                                                self.wind_bearing, self.humidity,
                                                                self.precip_chance, self.precip_type))
        con.commit()

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
    
def do_aggregatesql(service_name, data):
    forecast = ast.literal_eval(data)
    forecast = handle_format(forecast, fname)

    # Make sure we actually have the right data
    if 'currently' in forecast and 'temperature' in forecast['currently']:
        new_data = WeatherData(forecast['currently'])
        new_data.insert_sql(service_name)

    if 'hourly' in forecast:
        for fcast in forecast['hourly']['data']:
            new_forecast = HourlyForecastData(forecast['currently']['time'], fcast)
            # We don't care about forecasts made the day of
            if new_forecast.forecasted_time < new_forecast.timestamp:
                new_forecast.insert_sql(service_name)

    for fcast in forecast['daily']['data']:
        new_forecast = ForecastData(forecast['currently']['time'], fcast)
        # We don't care about forecasts made the day of
        if new_forecast.forecasted_time < new_forecast.timestamp:
            new_forecast.insert_sql(service_name)

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
                
            do_aggregatesql(fname.split('-')[-1], contents)

    print('')

def aggregate(dir_name, analyze_dir, f_re=None):
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
            forecast = ast.literal_eval(contents)

            forecast = handle_format(forecast, fname)

            # Make sure we actually have the right data
            if 'currently' in forecast and 'temperature' in forecast['currently']:
                new_data = WeatherData(forecast['currently'])
                if not str(new_data.time.date()) in weather_data:
                    weather_data[str(new_data.time.date())] = []

                weather_data[str(new_data.time.date())].append(new_data)

            if 'hourly' in forecast:
                for fcast in forecast['hourly']['data']:
                    new_forecast = HourlyForecastData(forecast['currently']['time'], fcast)
                    # We don't care about forecasts made the day of
                    if new_forecast.forecasted_time < new_forecast.timestamp:
                        if not str(new_forecast.time.date()) in hourly_data:
                            hourly_data[str(new_forecast.time.date())] = []

                        hourly_data[str(new_forecast.time.date())].append(new_forecast)

            for fcast in forecast['daily']['data']:
                new_forecast = ForecastData(forecast['currently']['time'], fcast)
                # We don't care about forecasts made the day of
                if new_forecast.forecasted_time < new_forecast.timestamp:
                    if not str(new_forecast.time.date()) in daily_data:
                        daily_data[str(new_forecast.time.date())] = []

                    daily_data[str(new_forecast.time.date())].append(new_forecast)

    print('')

    try:
        os.mkdir(analyze_dir + 'currently/')
    except:
        pass

    try:
        os.mkdir(analyze_dir + 'hourly/')
    except:
        pass

    try:
        os.mkdir(analyze_dir + 'daily/')
    except:
        pass

    i = 0
    total = len(weather_data) + len(hourly_data) + len(daily_data)
    if len(weather_data) > 0:
        utility.empty_dir(analyze_dir + 'currently/')
        for date in weather_data:
            utility.show_bar(i, total, message='Writing (weather_data): ')
            i += 1
            with open(analyze_dir + 'currently/' + date + '.txt', 'w') as f:
                f.write(str(weather_data[date]))

    if len(hourly_data) > 0:
        utility.empty_dir(analyze_dir + 'hourly/')
        for date in hourly_data:
            utility.show_bar(i, total, message='Writing (hourly_data): ')
            i += 1
            with open(analyze_dir + 'hourly/' + date + '.txt', 'w') as f:
                f.write(str(hourly_data[date]))

    if len(daily_data) > 0:
        utility.empty_dir(analyze_dir + 'daily/')
        for date in daily_data:
            utility.show_bar(i, total, message='Writing (daily_data): ')
            i += 1
            with open(analyze_dir + 'daily/' + date + '.txt', 'w') as f:
                f.write(str(daily_data[date]))

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
                    do_aggregatesql('darksky', str(forecast))
                elif service == 'yahoo':
                    print('Getting data from Yahoo for {}: {}'.format(location, format_date(now)))
                    forecast = get_yahoo_forecast(yahoo[location])
                    do_aggregatesql('yahoo', str(forecast))
                elif service == 'accuweather':
                    print('Getting data from Accuweather for {}: {}'.format(location, format_date(now)))
                    forecast = get_accuweather_forecast(accuweather[location])
                    do_aggregatesql('accuweather', str(forecast))
                elif service == 'wunderground':
                    print('Getting data from Weather Underground for {}: {}'.format(location, format_date(now)))
                    forecast = get_wunderground_forecast(location)
                    do_aggregatesql('wunderground', str(forecast))
                elif service == 'openweathermap':
                    print('Getting data from OpenWeatherMap for {}: {}'.format(location, format_date(now)))
                    forecast = get_openweathermap_forecast(location)
                    do_aggregatesql('openweathermap', str(forecast))

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

def monitor(locations, dir_name, freq, times=-1):
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
                    with open(dir_name + str(now.date()) + '/' + str(now.time()).replace(':','-') + '-darksky.txt', 'w') as f:
                        f.write(str(forecast))
                elif service == 'yahoo':
                    print('Getting data from Yahoo for {}: {}'.format(location, format_date(now)))
                    forecast = get_yahoo_forecast(yahoo[location])
                    with open(dir_name + str(now.date()) + '/' + str(now.time()).replace(':','-') + '-yahoo.txt', 'w') as f:
                        f.write(str(forecast))
                elif service == 'accuweather':
                    print('Getting data from Accuweather for {}: {}'.format(location, format_date(now)))
                    forecast = get_accuweather_forecast(accuweather[location])
                    with open(dir_name + str(now.date()) + '/' + str(now.time()).replace(':','-') + '-accuweather.txt', 'w') as f:
                        f.write(str(forecast))
                elif service == 'wunderground':
                    print('Getting data from Weather Underground for {}: {}'.format(location, format_date(now)))
                    forecast = get_wunderground_forecast(location)
                    with open(dir_name + str(now.date()) + '/' + str(now.time()).replace(':','-') + '-wunderground.txt', 'w') as f:
                        f.write(str(forecast))
                elif service == 'openweathermap':
                    print('Getting data from OpenWeatherMap for {}: {}'.format(location, format_date(now)))
                    forecast = get_openweathermap_forecast(location)
                    with open(dir_name + str(now.date()) + '/' + str(now.time()).replace(':','-') + '-openweathermap.txt', 'w') as f:
                        f.write(str(forecast))

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

def dump(analyze_dirs, xvar, yvars, datefilter, min_date, max_date, fname=None):
    def get_data(path):
        datas = [] # Yes I know data is already plural. Bite me
        with open(path, 'r') as f:
            contents = f.read()
        data = ast.literal_eval(contents)

        for yvar in yvars:
            datas.append([])

        for d in data:
            if datefilter != None:
                if datetime.datetime.utcfromtimestamp(d['timestamp']).date() != datefilter.date():
                    continue

            if min_date != None:
                if datetime.datetime.utcfromtimestamp(d['timestamp']).date() < min_date.date():
                    continue

            if max_date != None:
                if datetime.datetime.utcfromtimestamp(d['timestamp']).date() > max_date.date():
                    continue

            for i, yvar in enumerate(yvars):
                if yvar in d:
                    datas[i].append((d[xvar], d[yvar]))

        return datas

    if xvar == 'first':
        xvar = 'timestamp'

    paths = []

    if analyze_dirs != None:
        for analyze_dir in analyze_dirs:
            paths.extend(utility.get_files(analyze_dir))
    if fname != None:
        paths.append(fname)
    all_data = []
    for i, fname in enumerate(paths):
        utility.show_bar(i, len(paths), message='Dumping ({} of {}): '.format(i, len(paths)))
        all_data.append(get_data(fname))

    print('')

    res = []

    for yvar in yvars:
        res.append([])

    for data in all_data:
        for i, d in enumerate(data):
            res[i].extend(d)

    return res

# Because we have a bunch of forecasts for each day, we need to combine them all together
# There are number of ways to do this:
# first - Takes the first (chronologically) forecast and just uses that.
# last - Takes the last forecast and uses that.
# decay - Weights each forecast by the number of hours that it has been since the forecast was made.
#         Older forecasts are weighted less. The weight for a forecast is decay_rate**(-number of hours forecasted before day)
# average - Weights each forecast equally, and simply returns their arithmetic mean.
# median - The median.
def combine(analyze_dir, decay_rate, method):
    res = []
    fs = utility.get_files(analyze_dir)
    for i, fname in enumerate(fs):
        utility.show_bar(i, len(fs), message='Combining ({}): '.format(method))
        with open(fname, 'r') as f:
            contents = f.read()
        data = ast.literal_eval(contents)

        averaged = {}
        total = 0

        if method == 'first':
            for k,v in data[0].iteritems():
                if isinstance(v, (int, long, float)):
                    averaged[k] = v
        elif method == 'last':
            for k,v in data[-1].iteritems():
                if isinstance(v, (int, long, float)):
                    averaged[k] = v
        else:
            for d in data:
                # Hours instead of seconds should give us a more reasonable decay rate
                timestamp = (d['timestamp'] - d['forecasted_time']) / 3600
                for k,v in d.iteritems():
                    if isinstance(v, (int, long, float)):
                        if not k in averaged:
                            if method == 'decay':
                                averaged[k] = v * decay_rate**(-timestamp)
                            elif method == 'average':
                                averaged[k] = v
                            elif method == 'median':
                                averaged[k] = [v]
                        else:
                            if method == 'decay':
                                averaged[k] += v * decay_rate**(-timestamp)
                            elif method == 'average':
                                averaged[k] += v
                            elif method == 'median':
                                averaged[k].append(v)

                if method == 'decay':
                    total += decay_rate**(-timestamp)
                elif method == 'average':
                    total += 1

            for k in data[0]:
                if k in averaged:
                    if method == 'median':
                        averaged[k] = utility.median(averaged[k])
                    else:
                        averaged[k] /= total

        averaged['timestamp'] = data[0]['timestamp']
        res.append(averaged)

    print('')

    return res

def precip_accuracy(data):
    res = []

    for d in data:
        x = d.pop(0)
        y = 0
        for i in d:
            if i > 0.99:
                y = 1
                break

        res.append((x,y))

    return [res]

def do_plot(res, xvar, yvar, min_var, max_var, show_actual=False, join_f=None, data_f=None, graph_type='scatter', xmin=None, xmax=None, ymin=None, ymax=None, o=None):
    if show_actual or o == None:
        print('Plotting...')

    new_data = []

    # We like inner joins
    if join_f != None:
        possible = {}
        for vs in res:
            for (x, y) in vs:
                val = join_f(x)
                if val in possible:
                    possible[val].append(y)
                else:
                    possible[val] = [y]

        new_data = filter(lambda i: len(i) > 1, possible.values())

        if data_f != None:
            new_data = data_f(new_data)

        plot_values(new_data, '', yvar, min_var, max_var, show_actual, graph_type, xmin, xmax, ymin, ymax, o)
    else:
        plot_values(res, xvar, yvar, min_var, max_var, show_actual, graph_type, xmin, xmax, ymin, ymax, o)

def plot_values(res, xvar, yvar, min_var, max_var, show_actual, graph_type, xmin, xmax, ymin, ymax, o):
    min_ranges = []
    actual_mins = {}
    max_ranges = []
    actual_maxes = {}
    out_of_range = []
    for ci, (vs, yv) in enumerate(zip(res, yvar)):
        if show_actual or o == None:
            print('Plotting var: {}'.format(yv))

        # If it's the minimum variable or the maximum variable, then keep track and plot it separately.
        if yv == min_var and not 'box' in graph_type:
            for i, (x, y) in enumerate(vs):
                if i != len(vs) - 1:
                    next_x = vs[i + 1][0]
                    min_ranges.append((x,next_x,y))

                    if show_actual or o == None:
                        plt.plot([x, next_x], [y,y], COLORS[ci] + '-', linewidth=3.0)
                else:
                    min_ranges.append((x,x,y))
            min_ranges = sorted(min_ranges, reverse=True)

            if show_actual or o == None:
                print('Finished getting min_var values.')
        elif yv == max_var and not 'box' in graph_type:
            for i, (x, y) in enumerate(vs):
                if i != len(vs) - 1:
                    next_x = vs[i + 1][0]
                    max_ranges.append((x,next_x,y))

                    if show_actual or o == None:
                        plt.plot([x, next_x], [y,y], COLORS[ci] + '-', linewidth=3.0)
                else:
                    max_ranges.append((x,x,y))
            max_ranges = sorted(max_ranges, reverse=True)

            if show_actual or o == None:
                print('Finished getting max_var values.')
        elif not yv in [min_var, max_var] and (min_var != None or max_var != None):
            rep_data = []

            while len(vs) > 0:
                (x, y) = vs.pop(0)

                # If this data is outside all of our min and max ranges, we don't really care about it.
                is_in_a_range = False
                found = False
                for (min_x, max_x, v) in min_ranges:
                    if x > min_x and x < max_x:
                        is_in_a_range = True
                        if (min_x, max_x, v) in actual_mins:
                            if y < actual_mins[(min_x, max_x, v)]:
                                actual_mins[(min_x, max_x, v)] = y
                        else:
                            actual_mins[(min_x, max_x, v)] = y

                        if y < v:
                            out_of_range.append((x,y))
                            found = True
                            break
                if found:
                    continue
                for (min_x, max_x, v) in max_ranges:
                    if x > min_x and x < max_x:
                        is_in_a_range = True
                        if (min_x, max_x) in actual_maxes:
                            if y > actual_maxes[(min_x, max_x)]:
                                actual_maxes[(min_x, max_x, v)] = y
                        else:
                            actual_maxes[(min_x, max_x, v)] = y
                        if y > v:
                            out_of_range.append((x,y))
                            found = True
                            break
                if not found:
                    if is_in_a_range:
                        rep_data.append((x,y))

            vs = rep_data
            res[ci] = vs

        if 'scatter' in graph_type:
            if show_actual or o == None:
                plt.plot(map(utility.fst, vs), map(utility.snd, vs), COLORS[ci] + 'o', label=yv)
        elif 'line' in graph_type:
            if show_actual or o == None:
                plt.plot(map(utility.fst, vs), map(utility.snd, vs), COLORS[ci] + '-', label=yv)
        elif 'hist' in graph_type:
            params = graph_type.split(':')
            bins = 10
            if len(params) > 1:
                bins = int(params[1])

            if show_actual or o == None:
                plt.hist(map(utility.snd, vs), bins, histtype='bar', color=COLORS[ci], label=yv)
        elif 'bar' in graph_type:
            params = graph_type.split(':')
            inc = 0.1
            if len(params) > 1:
                inc = float(params[1])
            data = {}

            # Fill the data with 0s if we have a range to fill
            if xmin != None and xmax != None:
                xmin = float(xmin)
                xmax = float(xmax)
                for i in np.arange(xmin, xmax, inc):
                    data[i] = (0.0, 0.0)

            for (x, y) in vs:
                v = utility.round_nearest(x, inc)
                if not v in data:
                    data[v] = (y, 1.0)
                else:
                    cur, total = data[v]
                    data[v] = (cur + y, total + 1)

            print(data)

            xs = []
            ys = []
            for x, (cur, total) in data.iteritems():
                xs.append(x)
                if total > 0:
                    ys.append(cur / total)
                else:
                    ys.append(0)

            print(zip(xs, ys))

            if show_actual or o == None:
                plt.bar(xs, ys, inc * 0.9, color=COLORS[ci], label=yv)
                plt.xticks(xs)
        elif 'box' in graph_type:
            # Group the values by x
            groups = utility.group_and_sort_by(utility.fst, vs)
            group_vals = map(lambda i: (i[0][0], map(utility.snd, i)), groups)

            if all(map(lambda i: len(i) == 1, groups)):
                plt.plot(map(utility.fst, vs), map(utility.snd, vs), COLORS[ci] + 'o', label=yv, rasterized=True)
                continue

            if len(group_vals) > 1:
                x_dist = group_vals[1][0] - group_vals[0][0]
            else:
                x_dist = 0.05 * group_vals[0][0]

            box_width = x_dist / 3
            labeled = False

            for i, (actual_x, group) in enumerate(group_vals):
                x = actual_x + x_dist / 2
                if len(group) == 1:
                    if not labeled:
                        plt.plot([x], group[0], COLORS[ci] + 'o', label=yv)
                        labeled = True
                    else:
                        plt.plot([x], group[0], COLORS[ci] + 'o')
                else:
                    (smin, q1, m, q3, smax), lower_outliers, upper_outliers = utility.five_number_summary(group)

                    if i != len(group_vals) - 1:
                        next_x = group_vals[i + 1][0]

                        if yv == max_var:
                            max_ranges.append((actual_x,next_x,m))
                        elif yv == min_var:
                            min_ranges.append((actual_x,next_x,m))
                        if yv == max_var or yv == min_var:
                            plt.plot([actual_x, next_x], [m,m], COLORS[ci] + '-', linewidth=3.0)
                    else:
                        if yv == max_var:
                            max_ranges.append((actual_x,x,m))
                        elif yv == min_var:
                            min_ranges.append((actual_x,x,m))

                    if show_actual or o == None:
                        plt_vals = lower_outliers + upper_outliers

                        # Plot all the things that should be points
                        if not labeled:
                            plt.plot([x] * len(plt_vals), plt_vals, COLORS[ci] + 'o', label=yv)
                            labeled = True
                        else:
                            plt.plot([x] * len(plt_vals), plt_vals, COLORS[ci] + 'o')

                        # Plot the lines between the relevant points.
                        plt.plot([x] * 5, [smin, q1, m, q3, smax], COLORS[ci] + '-')

                        # Plot the boxes
                        # Plot the lines across
                        plt.plot([x - box_width, x + box_width], [q1,q1], COLORS[ci] + '-')
                        plt.plot([x - box_width, x + box_width], [m,m], COLORS[ci] + '-')
                        plt.plot([x - box_width, x + box_width], [q3,q3], COLORS[ci] + '-')

                        # Plot the verticle lines
                        plt.plot([x - box_width, x - box_width], [q1,q3], COLORS[ci] + '-')
                        plt.plot([x + box_width, x + box_width], [q1,q3], COLORS[ci] + '-')

        if show_actual or o == None:
            print('Plotted {}'.format(yv))

    # Let's convert these times into dates so the x axis is actually useful
    if 'time' in xvar and not 'hist' in graph_type:
        min_x = min(map(lambda i: min(map(utility.fst, i)), res))
        max_x = max(map(lambda i: max(map(utility.fst, i)), res))

        xticks_vs = []
        xticks = []

        one_day = datetime.timedelta(days=1)

        x = 0
        i = datetime.datetime.utcfromtimestamp(min_x)
        end = datetime.datetime.utcfromtimestamp(max_x)

        if show_actual or o == None:
            print('Data starts at {} and ends at {}'.format(i.date(), end.date()))

        every = math.ceil((end - i).days / 12.0)

        while i < end:
            if x % every == 0:
                xticks_vs.append(get_timestamp(i))
                xticks.append(i.strftime('%m-%d'))

            i += one_day
            x += 1

        if x % every == 0:
            xticks_vs.append(get_timestamp(i))
            xticks.append(i.strftime('%m-%d'))

    if len(out_of_range) > 0 and (show_actual or o == None):
        plt.plot(map(utility.fst, out_of_range), map(utility.snd, out_of_range), 'yo', label='Out of Range')
        print('Plotted out of range values.')

    if show_actual or o == None:
        if 'time' in xvar and not 'hist' in graph_type:
            plt.xticks(xticks_vs, xticks)

    mins_data = []
    for ((_,_,v),actual) in actual_mins.iteritems():
        mins_data.append(v - actual)

    maxes_data = []
    for ((_,_,v),actual) in actual_maxes.iteritems():
        maxes_data.append(v - actual)

    if show_actual and (len(actual_mins) > 0 or len(actual_maxes) > 0):
        print('----------------------------------------')
        print('Mins Stats:')
        if len(mins_data) > 0:
            m, s, (l, h) = utility.stats(mins_data)
            # print(mins_data)
            print('Mean: {}, Std. Dev: {}'.format(m, s))
            print('95%: {} to {}'.format(l, h))

        print('Maxes Stats:')
        if len(maxes_data) > 0:
            m, s, (l, h) = utility.stats(maxes_data)
            # print(maxes_data)
            print('Mean: {}, Std. Dev: {}'.format(m, s))
            print('95%: {} to {}'.format(l, h))

        print('----------------------------------------')


    if o != None:
        if not os.path.isfile(o):
            with open(o, 'w') as f:
                f.write('Sample Size,Min Mean,Min Std. Dev,Min Low,Min High,Max Mean,Max Std. Dev,Max Low,Max High\n')
        with open(o, 'a') as f:
            if len(mins_data) > 0:
                m, s, (l, h) = utility.stats(mins_data)
                f.write('{},{},{},{},{}'.format(len(mins_data), m, s, l, h))
            else:
                f.write('0,0,0,0')

            if len(maxes_data) > 0:
                m, s, (l, h) = utility.stats(maxes_data)
                f.write(',{},{},{},{}'.format(m, s, l, h))
            else:
                f.write(',0,0,0,0')

            f.write('\n')

    if show_actual or o == None:
        plt.legend()

        # Set the axes, if applicable
        x1,x2,y1,y2 = plt.axis()
        if xmin != None:
            x1 = float(xmin)
        if xmax != None:
            x2 = float(xmax)
        if ymin != None:
            y1 = float(ymin)
        if ymax != None:
            y2 = float(ymax)

        plt.axis((x1,x2,y1,y2))
        plt.show()

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

    if 'monitor' in args:
        if fname == None:
            print('Need a file that contains the list of locations to get data for.')
            return
        else:
            with open(fname, 'r') as f:
                contents = f.read()
            locations = ast.literal_eval(contents)
            monitor(locations, dir_name, freq, times=times)
    elif 'monitorsql' in args:
        if fname == None:
            print('Need a file that contains the list of locations to get data for.')
            return
        else:
            with open(fname, 'r') as f:
                contents = f.read()
            locations = ast.literal_eval(contents)
            monitorsql(locations, dir_name, freq, times=times)
    elif 'dump' in args:
        if 'yvar' in args:
            analyze_dir = args.get('analyze_dir', None)
            fname = args.get('f', None)
            xvar = args.get('xvar', 'timestamp')
            yvar = args.get('yvar', 'temp')
            outfile = args.get('out', None)

            if ',' in yvar:
                yvar = yvar.split(',')
            else:
                yvar = [yvar]
            if analyze_dir != None:
                if ',' in analyze_dir:
                    analyze_dir = analyze_dir.split(',')
                else:
                    analyze_dir = [analyze_dir]

            min_date = args.get('min_date', None)
            max_date = args.get('max_date', None)
            if min_date != None:
                min_date = parser.parse(min_date)
            if max_date != None:
                max_date = parser.parse(max_date)

            datefilter = args.get('date', None)
            if datefilter != None:
                datefilter = parser.parse(datefilter)

            # print('Getting ({}, {}) from: {}'.format(xvar, yvar, analyze_dir + dtype))

            res = dump(analyze_dir, xvar, yvar, datefilter, min_date, max_date, fname=fname)

            if 'graph' in args:
                graph_type = args.get('type', 'scatter')

                ymin = args.get('ymin', None)
                ymax = args.get('ymax', None)
                xmin = args.get('xmin', None)
                xmax = args.get('xmax', None)

                min_var = args.get('minvar', None)
                max_var = args.get('maxvar', None)

                join_f = eval(args.get('join', 'None'))
                data_f = eval(args.get('data', 'None'))

                show_actual = 'show_actual' in args
                o = args.get('o', None)

                do_plot(res, xvar, yvar, min_var, max_var, show_actual=show_actual, join_f=join_f, data_f=data_f, graph_type=graph_type, ymin=ymin, ymax=ymax, xmin=xmin, xmax=xmax, o=o)
            elif outfile != None:
                with open(outfile, 'w') as f:
                    f.write(str(res))
            else:
                print(res)
        else:
            print('Need a variable name for the y coordinate.')
    elif 'combine' in args:
        analyze_dir = args.get('analyze_dir', './analyze/daily/')
        method = args.get('method', 'decay')
        decay_rate = float(args.get('decay', '1.01'))
        outfile = args.get('o', None)

        res = combine(analyze_dir, decay_rate, method)
        if outfile == None:
            print(res)
        else:
            with open(outfile, 'w') as f:
                f.write(str(res))
    elif 'aggregate' in args:
        analyze_dir = args.get('analyze_dir', './analyze/')
        f_re = args.get('re', None)

        aggregate(dir_name, analyze_dir, f_re=f_re)
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
    
    con.close()
