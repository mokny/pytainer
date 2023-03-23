##############################################################
# socklib v1.0
# Multi-Connection Threaded TCP Server Module
# With Websocket support
# by Till Vennefrohne
##############################################################

import socket
import threading
import datetime
import uuid
import time
import ssl
import re
import struct
import errno
import sys, os
from hashlib import sha1
from base64 import b64encode
import urllib

FIN    = 0x80
OPCODE = 0x0f
MASKED = 0x80
PAYLOAD_LEN = 0x7f
PAYLOAD_LEN_EXT16 = 0x7e
PAYLOAD_LEN_EXT64 = 0x7f

OPCODE_CONTINUATION = 0x0
OPCODE_TEXT         = 0x1
OPCODE_BINARY       = 0x2
OPCODE_CLOSE_CONN   = 0x8
OPCODE_PING         = 0x9
OPCODE_PONG         = 0xA

#############
# TCP SERVER
#############

class Server(threading.Thread):
    def __init__(self, hostname, port, servertype = 'TCP'):
        super(Server, self).__init__()
        self.setName('Socklib Server Handler ' + hostname + str(port) + servertype)
        
        self.running = False
        self.hostname = hostname
        self.port = port
        self.connectionID = 0
        self.clientcount = 0
        self.clients = {}
        self.events = {}
        self.groups = {}
        self.routines = {}
        self.blockedIPs = []
        self.stringencoded = False
        self.datalen = 1024
        self.stopbyte = None
        self.attachstopbyte = True
        self.maxclients = 0
        self.websocket = False
        self.http = False
        self.lock = threading.Lock()

        if servertype == 'WEBSOCKET':
            self.websocket = True
            
        if servertype == 'HTTP':
            self.http = True
            
        return
    def error(self, code, msg):
        try:
            self.events["ERROR"](code, msg)
        except:
            pass
    def log(self, msg):
        try:
            self.events["LOG"](msg)
        except:
            pass
    def run(self):
        try:
            self.log("Creating Socket...")
            self.s = socket.socket()
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.log("Binding Socket to " + self.hostname + ":" + str(self.port) + "...")
            self.s.bind((self.hostname, self.port))
            self.s.listen()
            self.log("Server ready.")
        except Exception as e:
            self.log("Server error: " + str(e))
            self.error(1, "Server could not be started")
            return
        self.running = True
        while True:
            try:
                c, addr = self.s.accept()
                self.connectionID = self.connectionID + 1
                try:
                    self.log("Incoming connection from " + str(addr))
                    self.events["PRECONNECT"](addr[0])
                except:
                    pass
                client = _ServerClient(self, c, addr, self.connectionID)
                client.start()
            except Exception as e:
                self.log("Server error " + str(e))
                self.events["ERROR"](2, e)
                pass
        self.s.close()
        self.running = False
        return
    def setHandler(self, event, callback):
        self.log("Handler " + event + " created.")
        self.events[event] = callback
        return
    def addGroup(self, groupname):
        if not groupname in self.groups:
            self.groups[groupname] = []
    def sendToAll(self, data):
        for client in self.clients:
            self.clients[client].send(data)
        return
    def sendToAllExcept(self, exceptname, data):
        for client in self.clients:
            if self.clients[client].name != exceptname:
                self.clients[client].send(data)
        return
    def sendToName(self, name, data):
        try:
            self.clients[name].send(data)
        except:   
            self.error(3, "Client not found")
    def sendToGroup(self, group, data):
        if group in self.groups:
            for client in self.groups[group]:
                client.send(data)
        return
    def routine(self, name, timeout, once, handler):
        r = _ServerRoutine(self)
        r.timeout = timeout
        r.once = once
        r.handler = handler
        r.name = name
        r.start()
        self.log("Routine " + name + " initialized.")
        return
    def block(self, ip):
        self.blockedIPs.append(ip)
        self.log("IP " + ip + " added to blocklist.")
        return
    def unblock(self, ip):
        self.blockedIPs.remove(ip)
        self.log("IP " + ip + " removed from blocklist.")

class _ServerRoutine(threading.Thread):
    def __init__(self, svr):
        super(_ServerRoutine, self).__init__()

        self.svr = svr
        self.timeout = 1
        self.once = False
        self.active = False
        self.name = "Unnamed Routine"
        self.runcount = 0
        self.setName('Socklib Server Routine Handler ' + self.svr.hostname + str(self.svr.port) + self.svr.servertype)
    def run(self):
        self.active = True
        while self.active:
            if not self.active:
                break
            time.sleep(self.timeout)
            self.runcount += 1
            try:
                self.handler(self)
                self.svr.log("Routine " + self.name + " executed.")
            except:
                self.svr.log("Routine " + self.name + " error. Could not execute handler.")
            if self.once:
                self.svr.log("Routine " + self.name + " exited due to once condition.")
                break
        return
    def stop(self):
        self.active = False
        return

class _ServerClient(threading.Thread):
    def __init__(self, svr, connection, addr, id):
        super(_ServerClient, self).__init__()
        self.connected = True
        self.vars = {}
        self.connection = connection
        self.addr = addr
        self.svr = svr
        self.ip = addr[0]
        self.port = addr[1]
        self.id = id
        self.setName('client_' + str(uuid.uuid4()))
        self.groups = {}
        self.svr.clientcount = self.svr.clientcount + 1
        self.time_connect = datetime.datetime.now()
        self.time_lastdata = datetime.datetime.now()
        self.svr.log("Client Thread initialized")
        self.wshandshakedone = False
        self.sendlock = threading.Lock()
        #self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)

        if self.ip in self.svr.blockedIPs:
            self.svr.log("Client found in block list")
            try:
                self.svr.events["BLOCKED"](self, addr)
            except:
                pass
            self.disconnect()
            return
        if (self.svr.maxclients > 0) and (self.svr.clientcount > self.svr.maxclients):
            self.svr.log("Disconnecting client due to maxclients restriction")
            self.svr.error(5, "Maximum clients reached (" + str(self.svr.maxclients) + ")")
            self.disconnect()
        try:
            self.svr.events["CONNECT"](self,addr)
        except:
            pass
    def calculate_response_key(self, key):
        GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        hash = sha1(key.encode() + GUID.encode())
        response_key = b64encode(hash.digest()).strip()
        return response_key.decode('ASCII')   
    def make_handshake_response(self, key):
        return \
          'HTTP/1.1 101 Switching Protocols\r\n'\
          'Upgrade: websocket\r\n'              \
          'Connection: Upgrade\r\n'             \
          'Sec-WebSocket-Version: 13\r\n'        \
          'Sec-WebSocket-Accept: %s\r\n'        \
          '\r\n' % self.calculate_response_key(key)
    def sendws(self,message):
        header = bytearray()
        payload = self.encode_to_UTF8(message)
        payload_length = len(payload)

        # Normal payload
        if payload_length <= 125:
            header.append(FIN | OPCODE_TEXT)
            header.append(payload_length)

        # Extended payload
        elif payload_length >= 126 and payload_length <= 65535:
            header.append(FIN | OPCODE_TEXT)
            header.append(PAYLOAD_LEN_EXT16)
            header.extend(struct.pack(">H", payload_length))

        # Huge extended payload
        elif payload_length < 18446744073709551616:
            header.append(FIN | OPCODE_TEXT)
            header.append(PAYLOAD_LEN_EXT64)
            header.extend(struct.pack(">Q", payload_length))

        else:
            print("TOO LONG MESSAGE")
        response = header + payload

        with self.sendlock:
            self.connection.sendall(response)
    def encode_to_UTF8(self, data):
        try:
            return data.encode('UTF-8')
        except UnicodeEncodeError as e:
            print(e)
            return False
        except Exception as e:
            print(e)
            return False        
    def read_bytes(self, num):
        return self.rfile.read(num)        
    def run(self):
        stopbuffer = b''
        httpbuffer = ''
        httppackets = 0

        while self.connected:
            try:
                if (self.svr.websocket and not self.wshandshakedone) or not self.svr.websocket:
                    data = self.connection.recv(self.svr.datalen)
                    if not data:
                        break
                elif self.svr.websocket and self.wshandshakedone:
                    self.rfile = self.connection.makefile('rb', -1)

                self.time_lastdata = datetime.datetime.now()

                if self.svr.websocket and not self.wshandshakedone:
                    req = data.decode("utf-8").strip()
                    self.wshandshakedone = True
                    x = re.findall("Sec-WebSocket-Key: .*\r", req)
                    skey = x[0]
                    skey = skey.replace("Sec-WebSocket-Key: ","")
                    skey = skey.replace("\r","")
                    self.connection.sendall(self.make_handshake_response(skey).encode())
                    self.svr.log("WS Handshake sent")
                    self.svr.events["HANDSHAKE"](self, skey)

                elif self.svr.websocket and self.wshandshakedone:
                    try:
                        b1,b2 = self.read_bytes(2)
                    except ConnectionResetError as e:
                        if e.errno == errno.ECONNRESET:
                            self.svr.log("WS Client closed connection.")
                            break
                        b1, b2 = 0, 0                        
                    except ValueError as e:
                        b1, b2 = 0, 0

                    fin    = b1 & FIN
                    opcode = b1 & OPCODE
                    masked = b2 & MASKED
                    payload_length = b2 & PAYLOAD_LEN

                    if opcode == OPCODE_CLOSE_CONN:
                        self.svr.log("WS Client requests close connection")
                        break
                    if not masked:
                        self.svr.log("WS Request not masked")
                        break
                    if opcode == OPCODE_CONTINUATION:
                        self.svr.log("WS Continuation Frames are not supported")
                        break
                    elif opcode == OPCODE_BINARY:
                        self.svr.log("WS Binary Frames are not supported")
                        break
                    elif opcode == OPCODE_TEXT:
                        self.svr.log("WS Text Frame received")
                        pass
                    elif opcode == OPCODE_PING:
                        self.svr.log("WS Ping Frame received")
                        pass
                    elif opcode == OPCODE_PONG:
                        self.svr.log("WS Pong Frame received")
                        pass
                    else:
                        self.svr.log("WS Unknown Frame received")
                        break

                    if payload_length == 126:
                        payload_length = struct.unpack(">H", self.rfile.read(2))[0]
                    elif payload_length == 127:
                        payload_length = struct.unpack(">Q", self.rfile.read(8))[0]

                    masks = self.read_bytes(4)
                    message_bytes = bytearray()
                    for message_byte in self.read_bytes(payload_length):
                        message_byte ^= masks[len(message_bytes) % 4]
                        message_bytes.append(message_byte)
                    self.svr.events["DATA"](self, message_bytes.decode('utf8'))
                    pass

                elif self.svr.http:
                    httppackets+=1
                    data = data.decode("utf-8")
                    httpbuffer+=data
                    httpdata = httpbuffer.split("\r\n\r\n",2)

                    data = httpbuffer
                    fields = data.split("\r\n")
                    output = {}
                    get = {}
                    post = {}
                    filename = ''
                    isPost = False

                    for field in fields:
                        v = field.split(':')#split each line by http field name and value
                        if field.startswith('GET '):
                            spl = field.split("?",2)
                            if len(spl) > 1:
                                filename = spl[0].replace('GET ','')
                                spl = spl[1].split(" ")
                                getdata = spl[0].replace('/','')
                                parts = getdata.split('&')
                                for part in parts:
                                    if '=' in part:
                                        r = part.split("=")
                                        get[r[0]] = r[1]
                                    else:
                                        get[part] = True

                        if field.startswith('POST '):
                            isPost = True
                            spl = field.split("?",2)
                            if len(spl) > 1:
                                filename = spl[0].replace('POST ','')
                                spl = spl[1].split(" ")
                                getdata = spl[0].replace('/','')
                                parts = getdata.split('&')
                                for part in parts:
                                    if '=' in part:
                                        r = part.split("=")
                                        get[r[0]] = r[1]
                                    else:
                                        get[part] = True


                        if len(v) == 2:
                            output[v[0].strip().upper()] = v[1].strip()

                    if isPost:
                        mdata = data.split("\r\n\r\n",2)
                        if len(mdata) == 2:
                            post = dict(urllib.parse.parse_qsl(mdata[1]))


                    if int(output['CONTENT-LENGTH']) == len(httpdata[1]):
                        self.svr.attachstopbyte = False
                        self.send('HTTP/1.0 200 OK\r\n')
                        self.send("Access-Control-Allow-Origin: *\r\n")
                        self.send("Content-Type: text/html\r\n\r\n")
                        self.svr.events["DATA"](self, {'header_raw': data, 'header': output, 'get': get, 'post': post, 'filename': filename})
                        httpbuffer = ''
                        self.disconnect()
                else:
                    if self.svr.stopbyte is None:
                        if self.svr.stringencoded == True:
                            data = data.decode("utf-8").strip()
                        try:
                            self.svr.events["DATA"](self, data)
                        except Exception as ex:
                            print(f"Unexpected {ex=}, {type(ex)=}")
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            print(exc_type, fname, exc_tb.tb_lineno)                
                            pass
                    else:
                        stopbuffer += data
                        parts = stopbuffer.split(self.svr.stopbyte, 1)
                        while len(parts) == 2:
                            try:
                                message = parts[0]
                                if self.svr.stringencoded == True:
                                    message = message.decode("utf-8").strip()
                                self.svr.events["DATA"](self, message)
                            except Exception as ex:
                                print(f"Unexpected {ex=}, {type(ex)=}")
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                print(exc_type, fname, exc_tb.tb_lineno)                
                                pass 
                            stopbuffer = parts[1]
                            parts = stopbuffer.split(self.svr.stopbyte, 1)
                        stopbuffer = parts[0]

            except Exception as ex:
                print(f"Unexpected {ex=}, {type(ex)=}")
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)                
                #break
        self.disconnect()
        return
    def setName(self, newname):
        if newname in self.svr.clients:
            self.svr.log("Duplicate client name - Can not assign new name")
            return False
        else:
            self.svr.clients.pop(self.name, None)
            self.name = newname
            self.svr.clients[self.name] = self
            self.svr.log("New client name assigned")
            return True
    def addToGroup(self, groupname):
        self.svr.log("Client added to group " + groupname)
        self.svr.addGroup(groupname)
        try:
            self.svr.groups[groupname].remove(self)
        except:
            pass
        self.svr.groups[groupname].append(self)
    def removeFromGroup(self, groupname):
        self.svr.log("Client removed from group " + groupname)
        try:
            self.svr.groups[groupname].remove(self)
        except:
            pass
    def removeFromAllGroups(self):
        self.svr.log("Client removed from all groups")
        for groupname in self.svr.groups:
            try:
                self.svr.groups[groupname].remove(self)
            except:
                pass
    def send(self, data):
        if self.svr.websocket:
            self.sendws(data)
        else:
            if isinstance(data, str):
                data = str.encode(data)
            try:
                if self.svr.attachstopbyte:
                    data += self.svr.stopbyte
                self.connection.sendall(data)
            except Exception as ex:
                print(ex)
                self.disconnect()
        return
    def sendToAll(self, data):
        self.svr.sendToAll(data)
    def sendToAllExcept(self, exceptname, data):
        self.svr.sendToAllExcept(exceptname, data)
    def sendToName(self, name, data):
        self.svr.sendToName(name, data)
    def sendToGroup(self, group, data):
        self.svr.sendToGroup(group, data)
    def getTimeConnected(self):
        return datetime.datetime.now() - self.time_connect
    def getTimeInactive(self):
        return datetime.datetime.now() - self.time_lastdata
    def disconnect(self):
        if self.connected:        
            self.svr.log("Disconnecting client")
            self.connected = False
            with self.svr.lock:
                self.svr.clients.pop(self.name, None)
                self.removeFromAllGroups()
                try:
                    self.connection.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                self.connection.close()
                try:
                    self.svr.events["DISCONNECT"](self, self.addr)
                except:
                    pass
                self.svr.clientcount = self.svr.clientcount - 1
            self.svr.log("Client disconnected.")
        return

##############
# TCP CLIENT
##############

class Client(threading.Thread):
    def __init__(self, hostname, port):
        super(Client, self).__init__()
        self.hostname = hostname
        self.port = port
        self.connection = None
        self.events = {}
        self.connected = False
        self.reconnect = False
        self.reconnectdelay = 2
        self.maxreconnects = 10
        self.timeout = 10
        self.stringencoded = True
        self.datalen = 1024
        self.stopbyte = None
        self.attachstopbyte = True
        self._reconnectcount = 0
    def run(self):
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.connection:
                try:
                    try:
                        self.events["CONNECTING"](self)
                    except:
                        pass
                    self.connection.settimeout(self.timeout)
                    self.connection.connect((self.hostname, self.port))
                    self.connection.settimeout(None)
                    self.connected = True
                    try:
                        self.events["CONNECTED"](self)
                        self._reconnectcount = 0
                    except:
                        pass

                except:
                    pass
                stopbuffer = b''
                while True:
                    try:
                        data = self.connection.recv(self.datalen)
                        if not data:
                            break
                        if self.stopbyte is None:
                            try:
                                if self.stringencoded == True:
                                    data = data.decode("utf-8").strip()
                                self.events["DATA"](self, data)
                            except:
                                pass
                        else:
                            stopbuffer += data
                            parts = stopbuffer.split(self.stopbyte, 1)
                            while len(parts) == 2:
                                try:
                                    message = parts[0]
                                    if self.stringencoded == True:
                                        message = message.decode("utf-8").strip()
                                    self.events["DATA"](self, message)
                                except:
                                    pass 
                                stopbuffer = parts[1]
                                parts = stopbuffer.split(self.stopbyte, 1)
                            stopbuffer = parts[0]
                    except Exception as e:
                        break
                self.disconnect()
                if not self.reconnect:
                    break
                self._reconnectcount += 1
                if self._reconnectcount > self.maxreconnects:
                    if self.maxreconnects > 0:
                        break
                if self.reconnectdelay > 0:
                    time.sleep(self.reconnectdelay)
                self.events["RECONNECT"](self)
        self.events["TERMINATED"](self)
        return
    def setHandler(self, event, callback):
        self.events[event] = callback
        return
    def send(self, data):
        if self.connected:
            if isinstance(data, str):
                data = str.encode(data)
            try:
                if self.attachstopbyte:
                    data += self.stopbyte
                self.connection.sendall(data)
            except:
                self.disconnect()
    def disconnect(self):
        self.connected = False
        self.connection.close()
        try:
            self.events["DISCONNECTED"](self)
        except:
            pass

