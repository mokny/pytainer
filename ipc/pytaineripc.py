import threading
import time
from multiprocessing.connection import Listener
from multiprocessing.connection import Client
import uuid
import pathlib
import os
import copy
import sys

_version = "0"
_ipc = False
_abspath = str(pathlib.Path(__file__).parent.resolve())
_notifications = {}
_key = False
_clientport = False
_clientkey = False
_repos = False
# Get the running pyTainer Version
def getVersion():
    return do('VERSION')

# Notify other Repos with data. Data can be any object
def notify(repo, data):
    d = {
        'REPO': repo,
        'DATA': data
    }
    return do('NOTIFY', d)

# Get notifications from other Repos
def poll(repo):
    return do('POLL', repo)

# Stop a Repo
def stop(repo):
    return do('STOP', repo)

# Start a Repo
def start(repo):
    return do('START', repo)

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


##########################################################################


def _IPCServerSetVersion(version):
    global _version
    _version = version

def _IPCServerListen(port):
    global _ipc
    global _key
    import repos
    _key = str(uuid.uuid4())
    with open(_abspath+'/../tmp/ipcport.txt', 'w', encoding='utf-8') as f:
        f.write(str(port))    
    with open(_abspath+'/../tmp/ipckey.txt', 'w', encoding='utf-8') as f:
        f.write(str(_key))    
    _ipc = _IPCServer(port, _key, repos)
    _ipc.start()


class _IPCServer(threading.Thread):
    def __init__(self, port, key, repos):
        super(_IPCServer, self).__init__()
        self.setName('IPCServer')
        self.port = port
        self.listener = False
        self.conn = False
        self.running = False
        self.clients = {}
        self.key = key
        self.repos = repos
    def run(self):
        self.running = True
        self.listener = Listener(('localhost',self.port), authkey=self.key.encode())

        while self.running:
            conn = self.listener.accept()
            id = str(uuid.uuid4())
            self.clients[id] = _IPCServerClient(conn, id, self.repos)
            self.clients[id].start()

        self.listener.close()


class _IPCServerClient(threading.Thread):
    def __init__(self, conn, id, repos):
        super(_IPCServerClient, self).__init__()
        self.setName('IPCServerClient')
        self.conn = conn
        self.id = id
        self.repos = repos

    def run(self):
        self.running = True
        reply = {
            'OK': False,
            'DATA': False,
        }
        while self.running:
            try:
                msg = self.conn.recv()

                if msg['method'] == 'VERSION':
                    reply['OK'] = True
                    reply['DATA'] = _version
                elif msg['method'] == 'NOTIFY':
                    reply['OK'] = True
                    if not msg['payload']['REPO'] in _notifications:
                        _notifications[msg['payload']['REPO']] = []
                    _notifications[msg['payload']['REPO']].append(msg['payload']['DATA'])
                elif msg['method'] == 'POLL':
                    reply['OK'] = True
                    reply['DATA'] = []
                    if msg['payload'] in _notifications:
                        reply['DATA'] = copy.copy(_notifications[msg['payload']])
                        _notifications[msg['payload']] = []
                elif msg['method'] == 'START':
                    reply['OK'] = True
                    reply['DATA'] = "Starting " + msg['payload']
                    self.repos.exec(msg['payload'])
                elif msg['method'] == 'STOP':
                    reply['OK'] = True
                    reply['DATA'] = "Stopping " + msg['payload']
                    self.repos.stop(msg['payload'])
                else:
                    reply['ERR'] = 'Unknown Method'

                self.conn.send(reply)
            except Exception as ex:
                print(ex)
                self.running = False
                break
        self.conn.close()


