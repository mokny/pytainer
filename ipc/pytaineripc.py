import threading
import time
from multiprocessing.connection import Listener
from multiprocessing.connection import Client
import uuid
import pathlib
import os

ipc = False
abspath = str(pathlib.Path(__file__).parent.resolve())
print(abspath)

def send(msg):
    print("SEMDOMG" + abspath)
    try:
        with open(abspath+'/../tmp/ipcport.txt', 'r') as file:
            port = int(file.read())
        address = ('localhost', port)
        conn = Client(address, authkey=b'pytaineripc')
        conn.send(msg)
        conn.send('EXIT')
        conn.close()
        return True
    except:
        return False

def listen(port):
    with open(abspath+'/../tmp/ipcport.txt', 'w', encoding='utf-8') as f:
        f.write(str(port))    
    ipc = IPCServer(port)
    ipc.start()


class IPCServer(threading.Thread):
    def __init__(self, port):
        super(IPCServer, self).__init__()
        self.setName('IPCServer')
        self.port = port
        self.listener = False
        self.conn = False
        self.running = False
        self.clients = {}
    def run(self):
        self.running = True
        self.listener = Listener(('localhost',self.port), authkey=b'pytaineripc')

        while self.running:
            conn = self.listener.accept()
            id = str(uuid.uuid4())
            self.clients[id] = IPCServerClient(conn, id)
            self.clients[id].start()

        self.listener.close()


class IPCServerClient(threading.Thread):
    def __init__(self, conn, id):
        super(IPCServerClient, self).__init__()
        self.setName('IPCServerClient')
        self.conn = conn
        self.id = id

    def run(self):
        self.running = True

        while self.running:
            try:
                msg = self.conn.recv()
                print(msg)
            except:
                self.running = False
                break
        self.conn.close()


