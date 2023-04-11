# pyTainer
pyTainer is a python based container framework, that lets you manage predefined or custom programs. You can easily run/stop/restart/install/... all your containers via an intuitive web panel.

## Documentation
A complete guide is available here: https://github.com/mokny/pytainer/wiki

## Requirements
- Python 3.9.x

## Best use
Basically you can use one pyTainer to maintain all your programs. But as you can run multiple instances of pyTainer (on different ports), it might be a good idea to run one pyTainer for one project. For example: A pyhton server, a log manager, a notification service and a backup service runs on pyTainer A. Your smart home programs run on pyTainer B.

## Installation

### Manual installation
Download and extract pyTainer. Run the installation process:
```
chmod +x pytainer
./pytainer install
```
During the installation process, you will be asked for admin user credentials. Make sure to pick a secure username and password.

After completing the installation process, run pyTainer with the following command:
```
./pytainer start
```

For advanced debugging and live console output, you can use
```
./pytainer live
```

To stop pyTainer use
```
./pytainer stop
```

```
wget -O - https://raw.githubusercontent.com/mokny/pytainer/main/misc/install.sh | bash
```
#### Notice
When running pyTainer the first time, the python module `gitpython` will be automatically downloaded and installed via PIP.
