#Installation Instructions

First, install pip.

You should be able to do this by running:

```
python get-pip.py
```

Then, install both matplotlib and numpy as follows:

```
pip install matplotlib
pip install numpy
```

You should be able to run the main program (in collect_data.py) now.

Generally speaking, you don't need to touch collect_data.py as far as graphing goes, even though you can, because that's what all the bash scripts are for.
If you don't want to read the documentation for the dump command, just don't, and skip to the bash script documentation.
Instead, collect_data.py is only really used for gathering/aggregating data.

#Documentation for collect_data.py:
As all commands are used as follows

```
python collect_data.py COMMAND_NAME option=value option2=value2
```

Therefore, the "python collect_data.py" will be omitted.
Parameters ending in an '=' are options, meaning you must supply a value.
Order for options doesn't matter.
Options in parentheses are optional.

Commands:

```
aggregate [re=] [analyze_dir=]
```
Aggregating data from the directory given. Only open files whose name matches the regex given to re=.

```
monitor f= [dir=] [freq=] [times=]
```
Continually gathers data even 'freq' seconds, putting it in 'dir'. Runs for 'times' times, unless 'times' is -1, in which case it will run forever. Monitor files are a dictionary, with the keys being the name of the weather service and the value being the location you want to get the weather for. Currently, the only location supported for most services is 'southbend,us'. An example monitor file is in monitor.txt.

```
combine [analyze_dir=] [method=] [decay_rate=] [o=]
```

This function combines all the forecasts from multiple days into one (because data is typically taken once every 10 minutes, so there are many forecasts for each day).
- `analyze_dir` is where to get the data from.
- `method` can be one of the following:
- `first` takes the forecast that was made first (chronologically, of course) and simply uses those values.
- `last` takes the forecast that was made last.
- `decay` gives a weighted average of the forecasts, with the weight being decay_rate^(-hours between when forecast was made and day of forecast)
- `average` averages the forecasts, with each being weighted equally.
- `median` gets the median value for each value in the forecasts.
- `o` is a file to export the combined data to.

```
dump [analyze_dir=] [f=] [xvar=] yvar= [out=] [min_date=] [max_date=] [date=] [graph] [graph_type=] [ymin=] [ymax=] [xmin=] [xmax=] [minvar=] [maxvar=] [join_f=] [data_f=] [show_actual] [o=]
```
This is the main function for actual analysis. Generally speaking, you're better off not using this and using the bash scripts instead. Dump has two main functions: 1. Dump data into a graphable format. 2. Graph that data (if desired). The only argument that is required is `yvar`. It is either one or multiple (if multiple, then separated by commas) variables that should be plotted along the y axis. (e.g. `yvar=temp,temp_max,temp_min`)
- `xvar` is the variable plotted along the x axis. It is, by default, the timestamp on the data (converted to a more readable format on the actual graphs).
- `analyze_dir` is the directory that the data being analyzed is in.
- `f` a single file to read data from. Both this option and `analyze_dir` can be used (useful if all data is not in the same directory).
- `out` is a file to write out the dumped data to, but will only be used if the data is not graphed.
- `min_date` is a date (YYYY-MM-DD) that is a minimum (chronologically, of course) date for the data being dumped
- `max_date` is the same as min_date, but a maximum.
- `date` is if you only want data from one date.
- `graph` is the option that tells the program to actually graph the data (requires matplotlib/numpy).
- `graph_type` is the type of graph you want. Can be 'scatter', 'line', 'hist' (histogram), 'box' (box and whisker), or 'bar'. Not all graph types work for all types of data, obviously.
- `ymin`, `ymax`, `xmin`, and `xmax` are the boundaries for the graph created.
- `minvar` and `maxvar` specify which of the `yvar`s are boundaries for the rest. This is mainly useful for determining whether certain values (such as temperatures) are outside of desired ranges (predictions). Values that are outside the predicted range will be marked yellow.
- `join_f` is a python function that will be used to perform and inner join between two sets of values. It is used to transform the x values of the data.
- `data_f` is a python function that will be called on all of the data, allowing you to do pretty much whatever you want to it first.
- `show_actual` is a flag that determines whether the graph should be shown, or if the data should just be analyzed.
- `o` is a file name to export the mins and maxes stats (the mean and std dev, as well as a 95% confidence interval of the deviations of the actual mins and maxes from the predicted mins and maxes) to. Exports in a .csv format.

#Bash Script Documentation:
Order does matter here. Optional arguments are in `[]`, and most require a value, but none require the use of an equals sign.
All `analyze_dir`s are `'./analyze/daily/'` by default, or `'./analyze/$analyze_dir/'` if you specify.

```
plot_history.sh date <variable_name> <analyze_dir>
```
Plots the history of a variable over time for a given day. Variable name `'precip_chance'` by default.

```
plot_methods.sh
```
Gets the min and max stats for all services using all combine methods, and puts the data into data.csv. Row order is specified in the actual file itself.

```
plot_precip_accuracy.sh [inc] [method] [analyze_dir] [hourly|daily]
```
Plots a bar chart showing how often it actually rained on a given day versus what the predictions were. `inc` is the increment (by default 0.1, or every 10%). `method` is the method used to combine forecasts (by default decay), `hourly` or `daily` is whether to round time to the nearest hour or nearest day.

```
plot_precip_boxes.sh [analyze_dir]
```
Plots box and whisker plots for all precipitation predictions for all days in the given directory.

```
plot_precip_chance.sh [graph_type] [analyze_dir] [method]
```
Plots the `precip chance`, combining forecasts using `method`.

```
plot_temp_boxes.sh [range]
```
Plots the temperature for all days using the predicted maxes and mins (plotted with box and whisker plots) and the actual temperature (a scatter plot). If you want it to check the `range`, include that argument.

```
plot_temps.sh [method] [analyze_dir]
```
Plots the temperature for all days we have forecasts aggregated for, using the specified `method` to combine forecasts.

```
plot_var.sh [variable] [analyze_dir]
```
Plots the given variable for all days we have forecasts aggregated for.
