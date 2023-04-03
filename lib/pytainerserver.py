from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie

import time
import logger
import os
import random
import urllib
import apihandler
import uuid
import vars

sessions = {}

class clsPytainerServer(BaseHTTPRequestHandler):
    user = False
    sid = False
    cookie = SimpleCookie()

    def do_GET(self):
        #logger.info("New connection")
        try:
            self.handleRequest('GET', self.path, False)
        except Exception as ex:
            print(ex)
            pass

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        self.handleRequest('POST', self.path, post_data.decode("utf-8").strip())

    def generate_sid(self):
        sid = "".join(str(random.randint(1,9)) for _ in range(100))
        sid += str(uuid.uuid4()) + str(time.time())
        return sid

    def getSID(self):
        return self.sid

    def getSession(self):
        self.user = False
        self.sid = False
        cookies = SimpleCookie(self.headers.get('Cookie'))

        if "sid" in cookies:
            self.sid = cookies["sid"].value
            pass

        if self.sid:
            if self.sid in sessions:
                self.user = sessions[self.sid]

        if not self.user:
            self.sid = self.generate_sid()
            self.cookie['sid'] = self.sid
            sessions[self.sid] = {'address': self.client_address}
            self.user = sessions[self.sid]
        else:
            self.user = sessions[self.sid]
        #logger.info("SID: " + self.sid)
        #logger.info("USER: " + str(self.user))


    def sessionWrite(self, key, value):
        sessions[self.sid][key] = value
    
    def sessionGet(self, key):
        if key in sessions[self.sid]:
            return sessions[self.sid][key]
        return False

    def parse_cookies(self, cookie_list):
        return dict(((c.split("=")) for c in cookie_list.split(";"))) if cookie_list else {}

    def handleRequest(self, method, path, payload):
        if path == '/':
            path = '/index.html'

        #logger.info(path)
        #logger.info('...')
        if payload:
            payloaddata = urllib.parse.parse_qs(payload)
            payload = {}
            for p in payloaddata:
                if len(payloaddata[p]) > 0:
                    payload[p] = payloaddata[p][0]
        
        self.getSession()
        self.send_response(200)
        if path.endswith('.css'):
            self.send_header("Content-type", "text/css")
        elif path.endswith('.png'):
            self.send_header("Content-type", "image/png")    
        else:
            self.send_header("Content-type", "text/html")
        for morsel in self.cookie.values():
            self.send_header("Set-Cookie", morsel.OutputString())
        self.end_headers()

        if '.' in path:
            self.serveFile(path)
        else:
            apihandler.apiCall(self, path, payload)

    def reply(self, data):
        self.wfile.write(bytes(data, "utf-8"))

    def serveFile(self, path):
        if os.path.isfile(vars.path + '/ui' + path):
            if path.endswith('.png'):
                with open(vars.path + '/ui' + path, 'rb') as file_handle:
                    data = file_handle.read()    
                self.wfile.write(data)            
            else:
                file = open(vars.path + '/ui' + path, "r")
                data = file.read()
                file.close()            
                self.wfile.write(bytes(data, "utf-8"))
            
        else:
            self.wfile.write(bytes('oops', "utf-8"))

    def log_message(self, format, *args):
            #logger.info(args)
            return

def getSession(sid):
    if sid in sessions:
        return sessions[sid]
    return False

def listen(host, port):
    logger.info("Starting pyTainer Server")
    try:
        pyTainerServer = HTTPServer((host, port), clsPytainerServer)
        try:
            pyTainerServer.serve_forever()
        except KeyboardInterrupt:
            pass
    except Exception as ex:
        logger.error("Server could not be started: " + str(ex))
    try:
        pyTainerServer.server_close()
    except:
        pass
    logger.info("Server closed")
