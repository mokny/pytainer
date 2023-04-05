# pyTainer
pyTainer is a python based container framework, that lets you manage predefined or custom programs. You can easily run/stop/restart/install/... all your containers via an intuitive web panel.

## Requirements
- Python 3.9.x

## Best use
Basically you can use one pyTainer to maintain all your programs. But as you can run multiple instances of pyTainer (on different ports), it might be a good idea to run one pyTainer for one project. For example: A pyhton server, a log manager, a notification service and a backup service runs on pyTainer A. Your smart home programs run on pyTainer B.

## Installation

### Manual installation
Download and extract pyTainer. Run the installation process:
```
chmod +x pytainer.py
./pytainer.py -i fresh
```
During the installation process, you will be asked for admin user credentials. Make sure to pick a secure username and password.

After completing the installation process, run pyTainer with the following command:
```
./pytainer.py -l
```
You will notice that pyTainer is now running in the foreground with excessive logging (due to parameter `-l`). You can always terminate it by hitting `Ctrl+C`.

To run pyTainer in the background use the following command:

```
./pytainer.py --bg
```

#### Notice
When running pyTainer the first time, the python module `gitpython` will be automatically downloaded and installed via PIP.

## Advanced configuration
This is optional. pyTainer has good default settings that should suit your needs. But if you want to, edit the file `config.ini` at the main directory.
```ini
[WEBSERVER]
HOST = 0.0.0.0
PORT = 6880
SOCKETPORT = 6881

[IPC]
PORT = 6882

[LOGGING]
CONSOLELINES = 120

[REPOS]
ROOT = /my/path/where/i/wanna/store/programs

[DATABASE]
FILENAME = mydatabase.sqlite
```

## Accessing the Webpanel
In case you did not change settings inside the `config.ini`, simply call `http://<myipaddress>:6880`and login with your username and password.

## Installing programs on pyTainer
Open the Webpanel and navigate to `Install`. Here you can install apps from templates with one click, or enter a custom Github URL.

## Installing existing python scripts
Create a folder for your script inside the `pytainer/repos` directory. Copy your existing script to that directory. Create a `pytainer.toml` file at that directory, copy and paste the toml instructions below to that file and set `launcher` to your python file. That's it.

## Creating own pyTainer Programs from scratch
Getting started is quiet easy. Open the pyTainer Webpanel and navigate to `Install` -> `Create`. Now enter a uniqe ident, a title for your app and your name and click create. pyTainer will now create the `pytainer.toml` file and the `init.py` inside a dedicated project directory under `pytainer/repos`. More infos below.

There is also an example available [here](https://github.com/mokny/pytainer_example). Basically every simple python script can be a pyTainer program, as long as a valid `pytainer.toml` file exists.

## How pytainer.toml works
The pytainer.toml file is the initial file pyTainer looks for. It has to be located in the root directory of your app. If it does not exist, the app will not be recognized.
```python
[app]
ident = "unique_ident"
name = "My Appname"
version = "1.0"
launcher = "my_base_file.py"
language = "python"           #You may leave this blank, if its not a python app. Or set it to python3.9, python3.11 a.s.o
args = ""                     #Commandline args that have to be passed to the script
standalone = true             # Set this to false if you want to 
                              # run your app as pyTainer module,
                              # e.g. for communicating with other
                              # non-standalone apps.

[requirements]
modules = []
pytainerversion = '1.0'

[info]
author = "John Doe"
website = "http://example.com"

[config.myVariable1]
title = "My Variable 1"
description = "Enter a string value here"
type = "string"
value = "lala"

[config.myVariable2]
title = "My Variable 2"
description = "Enter an integer value here"
type = "int"
value = 123

[config.myVariable3]
title = "My Variable 3"
description = "Enter a float value here"
type = "float"
value = 123.456
```
As you can see above, `my_base_file.py` will be the python file that pyTainer will start. The `config.XXXXXX` sections define configuration variables that are passed to the app. These variables can be directly edited at the user interface!

### standalone = true or false?
Standalone apps will be launched as subprocess and will not be able to access pyTainers internal variables, or the thread they are running in. This is useful if you don't need these features. Standalone apps should also have the functionality of running without pyTainer. Within your script, you can detect if your app is running inside pyTainer, with the following code:
```
if not 'pytainerserver' in sys.modules:
    print("Not running as pyTainer Module, initializing manually.")
```

Non-Standalone apps will be launched as module of pyTainer. This has the advantage of quicker communication with other apps, receiving events etc.

Non-Standalone apps should implement the following global functions in the main file:
```python
def pytainer_init(app):
    # This gets called when your app was started
    # 'app' references the underlying thread. See the docs how to use.
    pass

def pytainer_stop(app):
    # This gets called when your app was stopped. Here you can do your cleanup, end threads etc...
    pass
```

## Running non Python Programs
tbd

## Making a backup
Making a backup is quiet easy. Just copy the complete pyTainer directory. This will backup everything, including users, programs etc. Note: Some programs may change files outside their repo directory. These changes have to be saved seperately!

# Communicate with other Repos or with pyTainer
To communicate with other apps or pyTainer, you have to import `pytaineripc`.

## Import the IPC Module
If your app is standalone, use this code:
```python
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.resolve()) + '/../../ipc')
import pytaineripc
```
If your app is NOT standalone simply do this:
```python
import pytaineripc
```

## Usage
The IPC Interface is easy to use. Sending data to another app works like this:
```python
# Create two functions that will handle Notifications and events
def pytainerNotificationHandler(data):
   print("Notification received:" + str(data))

def pytainerEventHandler(data):
   print("Event received:" + str(data))

# Initialize the IPC interface to receive notifications and events
pytaineripc.init(__file__, pytainerNotificationHandler, pytainerEventHandler) # Important: This has to be called from your main launcher file

# If you defined configuration options at your pytainer.toml file, this is how you get this data
config = pytaineripc.getConfig()

# This is how you send a notification to another app
response = pytaineripc.notify('APPIDENT', 'MESSAGE')
```
`MYIDENT` is the ident of your app, `APPIDENT` is the ident of a different app, `MESSAGE` can be just a string or any object.

You may also poll notifications manually - Note, this does NOT work for events!

```python
# Manual polling for new notifications
response = pytaineripc.poll('MYIDENT')
```
`MYIDENT` is the ident of the receiving app. Response data comes in an array. Call this function frequently to receive other apps notifications. Once polled, performe actions with the data. The next poll will be empty, unless new notifications for your app arrived.

You can also start and stop other apps:
```python
response = pytaineripc.start('OTHERAPPIDENT') # Run a different app
response = pytaineripc.stop('OTHERAPPIDENT') # Stop a different app
```

There are some more methods available:
```python
response = pytaineripc.getVersion() # Get pyTainer Version
response = pytaineripc.isRunning('OTHERAPPIDENT') # Check if a different app is running
response = pytaineripc.isAvailable('OTHERAPPIDENT') # Check if a different app is installed
response = pytaineripc.raiseEvent('MyCustomEvent') # Raise a custom event
pytaineripc.destroy() # Ends the ipc polling thread
```

## Events
Events are raised by pyTainer itself or by apps. Events are global, so every app will receive the events (as long as they implemented an event handler...). The IPC module polls for new events every second by default. You can increase the polling speed with `pytaineripc.setSpeed(0.1)` - the lower the value, the faster the poll interval. Event data is passed to your handler as a dictionary with the following keys: `TYPE`, `BY`, `PAYLOAD`. If `BY` is an empty string, the event was raised by pTainer itself.

If you raise a custom event with `pytaineripc.raiseEvent('MyCustomEvent', payload)` (payload is optional and can be any datatype - also objects), keep in mind that all apps will receive this event. So you might prefix the event with some ident. Example: `myapp.eventname`. 

## Notifications
Notifications are sent by one app to another app with `pytaineripc.notify('APPIDENT', 'MESSAGE')`. This notification will be only delivered to apps that were initialized with `APPIDENT`

# setup.pytainer
The optional `setup.pytainer` file is optional. It must be located in the main app directory. It's purpose is to setup your app on installation. The file can look like this:
```
# Run a command
RUN: ls -la

# Install a PIP package
PIPINSTALL: homeassistant-api

# Copy files from A to B
COPY: asd asd

# Download a file from the web to some location (location is always relative to the path of your app)
DL: https://somedomain.tld/file.txt somefolder/file.txt
```