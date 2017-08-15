# Installation Instructions

First, install pip (assuming you haven't done so already).

Then, install both matplotlib and numpy as follows:

```
pip install matplotlib
pip install numpy
```

You should be able to run the main program (in collect_data.py) now.

# Documentation for collect_data.py:
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
monitor f= [freq=] [times=]
```
Continually gathers data even 'freq' seconds, putting it in 'dir'. 
Runs for 'times' times, unless 'times' is -1, in which case it will run forever. 
Monitor files are a list of tuples, with the first item in the tuple being the name of the weather service and the second being the location you want to get the weather for. 
An example monitor file is in monitor.txt.

In order for this to work you must have API keys for all the relevant services you wish to use.
You must also have a MySQL server set up with an appropriately configured secrets.py file (obviously you cannot see mine).
Look at the top of collect_data.py for information on exactly what needs to be in the secrets file.

# Supported Services

- Darksky
- Yahoo (sort of)
- Accuweather
- Weather Underground
- Open Weather Map

