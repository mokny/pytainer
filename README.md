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
Basically you can simply create a new directory in the `repos` directory. Create a `pytainer.toml` file (see specifications below) and a main executable file. You can also install repositories from git by entering the URL and giving it a name.

## Creating own pyTainer Programs
There is an example available [here](https://github.com/mokny/pytainer_example). Basically every simple python script can be a pyTainer program, as long as the main file is called `init.py`.

## How pytainer.toml works
The pytainer.toml file is the initial file pyTainer looks for. It has to be located in the root directory of your app. If it does not exist, the app will not be recognized.
```python
[app]
ident = "unique_ident"
name = "My Appname"
version = "1.0"
requires = []
launcher = "my_base_file.py"
standalone = true             # Set this to false if you want to 
                              # run your app as pyTainer module,
                              # e.g. for communicating with other
                              # non-standalone apps.

[info]
author = "John Doe"
website = "http://example.com"
```
As you can see above, `my_base_file.py` will be the python file that pyTainer will start.

### standalone = true or false?
Standalone apps will be launched as subprocess and will not be able to access pyTainers internal variables, or the thread they are running in. This is useful if you don't need these features. Standalone apps should also have the functionality of running without pyTainer. Within your script, you can detect if your app is running inside pyTainer, with the following code:
```
if not 'pytainerserver' in sys.modules:
    print("Not running as pyTainer Module, initializing manually.")
```

Non-Standalone apps will be launched as module of pyTainer. This has the advantage of quicker communication with other apps, receiving events etc.

Non-Standalone apps should implement the following global functions in the main file:
```python
def pytainer_init(pyTainerThread):
    # This gets called when your app was started
    # 'pyTainerThread' references the underlying thread. See the docs how to use.
    pass

def pytainer_stop(pyTainerThread):
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

## Using IPC
The IPC Interface is easy to use. Sending data to another app works like this:
```python
response = pytaineripc.notify('APPIDENT', 'MESSAGE')
```
`APPIDENT` is the ident of the other app, `MESSAGE` can be just a string or any object.

To receive this data from another app, use this code:

```python
response = pytaineripc.poll('MYIDENT')
```
`MYIDENT` is the ident of the receiving app. Response data comes in an array. Call this function frequently to receive other apps notifications.

You can also start and stop other apps:
```python
response = pytaineripc.start('OTHERAPPIDENT')
response = pytaineripc.stop('OTHERAPPIDENT')
```

There are some more methods available:
```python
response = pytaineripc.getVersion()
```
