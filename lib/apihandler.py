import json
import users
import cryptolib
import repos
import logger
import config
import os
import psutil

def apiCall(request, path, data):
    response = {
        'OK': False,
        'AUTHED': False,
        'METHOD': path,
    }

    if request.sessionGet('user'):
        response['AUTHED'] = True

    if path == '/auth':
        if 'username' in data and 'password' in data:
            result = users.authenticate(data['username'], data['password'])
            if (result):
                request.sessionWrite('user', result)
                response['OK'] = True
                response['AUTHED'] = True
                response['USERNAME'] = result['username']
            else:
                request.sessionWrite('user', False)
                response['OK'] = False
                response['ERR'] = 'Invalid login'
                response['AUTHED'] = False
        else:    
            request.sessionWrite('user', False)
            response['OK'] = False
            response['ERR'] = 'Invalid login'
            response['AUTHED'] = True


    elif path == '/ready':
        if response['AUTHED']:
            response['OK'] = True
            response['SID'] = request.getSID()
            response['WSSP'] = config.getInt('WEBSERVER','SOCKETPORT',6881)

    elif path == '/repolist':
        if response['AUTHED']:
            response['OK'] = True
            response['DATA'] = repos.getList()

    elif path == '/execrepo':
        if response['AUTHED']:
            response['OK'] = True
            response['DATA'] = repos.exec(data['name'])

    elif path == '/stoprepo':
        if response['AUTHED']:
            response['OK'] = True
            response['SUCCESS'] = repos.stop(data['name'])

    elif path == '/removerepo':
        if response['AUTHED']:
            response['OK'] = True
            response['SUCCESS'] = repos.remove(data['name'])

    elif path == '/reloadrepos':
        if response['AUTHED']:
            response['OK'] = True
            response['SUCCESS'] = repos.scanFolder()

    elif path == '/gitfetch':
        if response['AUTHED']:
            if repos.gitfetch(data['url']):
                response['OK'] = True
            else:
                response['OK'] = False
                response['ERR'] = 'Repository could not be cloned'

    elif path == '/getlogs':
        if response['AUTHED']:
            response['OK'] = True
            response['DATA'] = logger.getHistory()

    elif path == '/getrepologs':
        if response['AUTHED']:
            response['OK'] = True
            response['DATA'] = repos.getOutput(data['name'])

    elif path == '/getrepodetails':
        if response['AUTHED']:
            response['OK'] = True
            response['DATA'] = repos.getDetails(data['name'])

    elif path == '/performance':
        if response['AUTHED']:
            load1, load5, load15 = psutil.getloadavg()

            response['OK'] = True
            response['DATA'] = {
                'cpupercent': psutil.cpu_percent(),
                'cpuusage': (load15/os.cpu_count()) * 100,
                'ramusedpercent': psutil.virtual_memory()[2],
                'ramusedgb': psutil.virtual_memory()[3]/1000000000,
            }


    else:
        response['ERR'] = 'Unknown Method'

    request.reply(json.dumps(response))
    