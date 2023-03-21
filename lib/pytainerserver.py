from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import logger
import os
import random
sessions = {}

class clsPytainerServer(BaseHTTPRequestHandler):
    def do_GET(self):
        logger.info("New connection")
        self.serveFile(self.path)
        pass

    def generate_sid(self):
        return "".join(str(random.randint(1,9)) for _ in range(100))

    def getSession(self):
        user = False
        sid = False
        try:
            cookies = self.parse_cookies(self.headers["Cookie"])
            if "sid" in cookies:
                user = cookies["sid"] if (cookies["sid"] in sessions) else False
        except:
            pass

        if not user:
            sid = self.generate_sid()
            cookie = "sid={}".format(sid)
            sessions[sid] = {'address': self.client_address}
            self.send_header('Set-Cookie', cookie)
            return sessions[sid]
        else:
            return sessions[user]

    def sendHeaders(self):
        self.send_header("Content-type", "text/html")
        session = self.getSession()
        self.end_headers()
        return session

    def parse_cookies(self, cookie_list):
        return dict(((c.split("=")) for c in cookie_list.split(";"))) if cookie_list else {}

    def serveFile(self, path):
        if path == '/':
            path = '/index.html'
        logger.info(path)
        if os.path.isfile('ui' + path):
            self.send_response(200)
            session = self.sendHeaders()

            handler(self,session)

            file = open('ui' + path, "r")
            data = file.read()
            file.close()            

            self.wfile.write(bytes(data, "utf-8"))
        else:
            self.send_response(404)
            self.sendHeaders()

    def log_message(self, format, *args):
            logger.info(args)
            return


def handler(request, session):
    logger.info("Handler!")
    logger.info(session)
    pass


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
