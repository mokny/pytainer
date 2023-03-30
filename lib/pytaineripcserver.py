

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

_abspath = str(pathlib.Path(__file__).parent.resolve())

_version = "0"
_ipc = False
_notifications = {}
_events = []
_key = False

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

def raiseEvent(type, payload):
    _events.append({'time':datetime.datetime.now(), 'event': type, 'by': '', 'payload': payload})
        
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
                elif msg['method'] == 'RAISEEVENT':
                    reply['OK'] = True
                    for _ev in copy.copy(_events):
                        if _ev['time'] < datetime.datetime.now()-datetime.timedelta(0,10):
                            _events.remove(_ev)
                    _events.append({'time':datetime.datetime.now(), 'event': msg['payload']['type'], 'by': msg['payload']['repo'], 'payload':  msg['payload']['payload']})
                elif msg['method'] == 'POLL':
                    reply['OK'] = True
                    reply['DATA'] = []
                    if msg['payload'] in _notifications:
                        reply['DATA'] = copy.copy(_notifications[msg['payload']])
                        _notifications[msg['payload']] = []
                elif msg['method'] == 'START':
                    reply['OK'] = True
                    reply['DATA'] = "Starting " + msg['payload']
                    self.repos.exec(msg['payload'], '')
                elif msg['method'] == 'STOP':
                    reply['OK'] = True
                    reply['DATA'] = "Stopping " + msg['payload']
                    self.repos.stop(msg['payload'])
                elif msg['method'] == 'ISRUNNING':
                    reply['OK'] = True
                    reply['DATA'] = self.repos.isRunning(msg['payload'])
                elif msg['method'] == 'ISAVAILABLE':
                    reply['OK'] = True
                    reply['DATA'] = self.repos.isAvailable(msg['payload'])
                    
                elif msg['method'] == '_AUTOPOLL':
                    reply['OK'] = True
                    reply['NOTIFICATIONS'] = []
                    reply['EVENTS'] = []

                    repo = msg['payload']['repo']
                    lastpoll = msg['payload']['lastpoll']
                    if repo in _notifications:
                        if _notifications[repo]:
                            reply['NOTIFICATIONS'] = copy.copy(_notifications[repo])
                            _notifications[repo] = []
                    for _ev in copy.copy(_events):
                        if _ev['time'] > lastpoll and not _ev['by'] == repo:
                            reply['EVENTS'].append(_ev)
                else:
                    reply['ERR'] = 'Unknown Method'

                self.conn.send(reply)
            except Exception as ex:
                print(ex)
                self.running = False
                break
        self.conn.close()


