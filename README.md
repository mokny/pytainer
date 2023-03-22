# pytainer
pyTainer is a python based container framework, that lets you manage predefined or custom programs. You can easily run/stop/restart/install/... all your containers via an intuitive web panel.

## Installation

### Manual installation
Download and extract pyTainer. Run the installation process:
```
./pyTainer.py -i fresh
```
During the installation process, you will be asked for admin user credentials. Make sure to pick a secure username and password.


## Installing programs on pyTainer
Basically you can simply create a new directory in the `repos` directory and add the `init.py` as the main executable file. You can also install repositories from git by entering the URL and giving it a name.