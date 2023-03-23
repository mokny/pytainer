import socklib
import config
import json
import pytainerserver
import logger

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
            else:
                client.vars['user'] = False
                send(client, 'AUTH', False)
        
        if 'user' in client.vars:
            pass
            
    except:
        pass

def onDisconnect(client, data):
    logger.info("DDDIIIIIIISSSSCOOOOO")

    if 'sid' in client.vars:
        del sessions[client.vars['sid']]
        logger.info("WSS SESSIONS")
        logger.info(sessions)
    pass

def init():
    server = socklib.Server(config.getStr('WEBSERVER','HOST','0.0.0.0'), config.getInt('WEBSERVER','SOCKETPORT',6881), 'WEBSOCKET')                  # Set the server to any hostname, port 50000
#vars.var['server_ui'].setHandler("HANDSHAKE", handler_ui.onHandshake)                  # Define Handler function for Server Log
#vars.var['server_ui'].setHandler("LOG", handler_ui.onLog)                  # Define Handler function for Server Log
#vars.var['server_ui'].setHandler("PRECONNECT", handler_ui.onPreConnect)    # Define Handler function for incoming connection
#vars.var['server_ui'].setHandler("CONNECT", handler_ui.onConnect)          # Define Handler function for connection established
#vars.var['server_ui'].setHandler("DISCONNECT", handler_ui.onDisconnect)    # Define Handler function for client disconnected
    server.setHandler("HANDSHAKE", onHandshake)                # Define Handler function for received data
    server.setHandler("DATA", onData)                # Define Handler function for received data
    server.setHandler("DISCONNECT", onDisconnect)                # Define Handler function for received data
#vars.var['server_ui'].setHandler("ERROR", handler_ui.onError)              # Define Handler function for Server-Errors
#vars.var['server_ui'].setHandler("BLOCKED", handler_ui.onBlocked)          # Define Handler function for Blocked IP handling
    server.start()