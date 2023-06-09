import threading
import time
from multiprocessing.connection import Listener
from multiprocessing.connection import Client
import uuid
import pathlib
import os
import copy
import sys
import json
import datetime
import sys
import __main__
#parent_module = sys.modules['.'.join(__name__.split('.')[:-1]) or '__main__']
#print(sys.modules['__main__'].__file__)
#print("####################" + str(parent_module))

_launcher = __main__.__file__
_abspath = str(pathlib.Path(__file__).parent.resolve())
_clientport = False
_clientkey = False
_initialized = False
_poller = False
_repoident = False



def _init(repo, notificationHandler = False, eventHandler = False):
    global _clientport
    global _clientkey
    global _initialized
    global _poller
    global _repoident
    if _initialized:
        return False
    
    if repo.startswith('/'):
        try:
            import toml as tomlreader
        except:
            import tomllib as tomlreader

        _repopath = str(pathlib.Path(repo).parent.resolve())
        if os.path.isfile(_repopath + '/pytainer.toml'):
            manifest = tomlreader.load(_repopath + '/pytainer.toml')
            repo = manifest['app']['ident']


    _repoident = repo
    if not _initialized:
        if not _clientport:
            with open(_abspath+'/../tmp/ipcport.txt', 'r') as file:
                _clientport = int(file.read())
            
        if not _clientkey:
            with open(_abspath+'/../tmp/ipckey.txt', 'r') as file:
                _clientkey = file.read()

        _poller = _PollHandler(repo, notificationHandler, eventHandler)
        _poller.start()
        
        _initialized = True
    return True

def setHandlers(notificationHandler, eventHandler):
    if _poller:
        _poller.notificationHandler = notificationHandler
        _poller.eventHandler = eventHandler
        return True
    return False
        
def setNotificationHandler(notificationHandler):
    if _poller:
        _poller.notificationHandler = notificationHandler
        return True
    return False        

def setEventHandler(eventHandler):
    if _poller:
        _poller.eventHandler = eventHandler
        return True
    return False        

def getIdent():
    return _repoident

def setIdent(ident):
    _repoident = ident

def destroy():
    if _poller:
        _poller.running = False

def setPollSpeed(speed):
    if _poller:
        if speed < 0.1:
            speed = 0.1
        _poller.speed = speed
        return True
    return False

# Clear all notifications
def clearNotifications():
    return do('CLEARNOTIFICATIONS', _repoident)

# Get the running pyTainer Version
def getVersion():
    return do('VERSION')

# Get config
def getConfig():
    try:
        with open(_abspath+'/../tmp/'+_repoident+'_config.json', 'r') as file:
            return json.loads(file.read())
    except:
        return {}

# Notify other Repos with data. Data can be any object
def notify(repo, data):
    d = {
        'REPO': repo,
        'DATA': data
    }
    return do('NOTIFY', d)

# Fire an event
def raiseEvent(type, payload = False):
    return do('RAISEEVENT', {'type': type, 'repo': _repoident, 'payload': payload})

# Get notifications from other Repos
def poll(repo = False):
    if not repo:
        repo = _repoident
    return do('POLL', repo)

# Stop a Repo
def stop(repo):
    return do('STOP', repo)

# Start a Repo
def start(repo):
    return do('START', repo)

# Check if a repo is running
def isRunning(repo):
    return do('ISRUNNING', repo)

# Check if a repo is running
def isAvailable(repo):
    return do('ISAVAILABLE', repo)

# Raw sending method
def do(method, payload = False):
    global _clientport
    global _clientkey

    d = {
        'method': method,
        'payload': payload
    }
    ret = False
    try:
        if not _clientport:
            with open(_abspath+'/../tmp/ipcport.txt', 'r') as file:
                _clientport = int(file.read())
            
        if not _clientkey:
            with open(_abspath+'/../tmp/ipckey.txt', 'r') as file:
                _clientkey = file.read()

        address = ('localhost', _clientport)
        conn = Client(address, authkey=_clientkey.encode())
        conn.send(d)
        running = True
        while running:
            while conn.poll():
                ret = conn.recv()
                running = False
        conn.close()
        return ret
    except Exception as ex:
        return False

class _PollHandler(threading.Thread):
    def __init__(self, repo, notificationHandler, eventHandler):
        super(_PollHandler, self).__init__()
        self.setName('IPCPollHandler')
        self.speed = 1
        self.notificationHandler = notificationHandler
        self.eventHandler = eventHandler
        self.repo = repo
        self.lastpoll = datetime.datetime.now()

    def run(self):
        self.running = True

        while self.running:
            time.sleep(self.speed)

            response = do('_AUTOPOLL', {'repo': self.repo, 'lastpoll': self.lastpoll})

            if response['NOTIFICATIONS']:
                if len(response['NOTIFICATIONS']) > 0:
                    if self.notificationHandler:
                        self.notificationHandler(response['NOTIFICATIONS'])
            if response['EVENTS']:
                if len(response['EVENTS']) > 0:
                    if self.eventHandler:
                        for _ev in response['EVENTS']:
                            self.eventHandler({'TYPE' : _ev['event'], 'BY': _ev['by'], 'PAYLOAD': _ev['payload']})

            self.lastpoll = datetime.datetime.now()



##### Init
_init(_launcher, False, False)