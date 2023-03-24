import socklib
import config
import json
import pytainerserver
import logger
import repos

server = False
sessions = {}

def send(client, method, data):
    s = {
        'M': method,
        'D': data
    }
    client.send(json.dumps(s))
    pass

def sendAll(method, data):
    for sid in sessions:
        send(sessions[sid], method, data)

def onHandshake(client,data):
    pass

def onData(client, data):
    try:
        data = json.loads(data)
        method = data['M']
        payload = data['D']
        if method == 'AUTH':
            session = pytainerserver.getSession(payload)
            if 'user' in session:
                client.vars['user'] = session['user']
                client.vars['sid'] = payload
                sessions[payload] = client
                send(client, 'AUTH', True)
                repos.sendOutput(client)
            else:
                client.vars['user'] = False
                send(client, 'AUTH', False)
        
        if 'user' in client.vars:
            pass
            
    except:
        pass


def onDisconnect(client, data):
    if 'sid' in client.vars:
        del sessions[client.vars['sid']]

def init():
    server = socklib.Server(config.getStr('WEBSERVER','HOST','0.0.0.0'), config.getInt('WEBSERVER','SOCKETPORT',6881), 'WEBSOCKET')                  # Set the server to any hostname, port 50000
    server.setHandler("HANDSHAKE", onHandshake)                # Define Handler function for received data
    server.setHandler("DATA", onData)                # Define Handler function for received data
    server.setHandler("DISCONNECT", onDisconnect)                # Define Handler function for received data
    server.start()