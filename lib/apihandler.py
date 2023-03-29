import json
import users
import cryptolib
import repos
import logger
import config
import os
import psutil
import vars
try:
    import toml as tomlreader
except:
    import tomllib as tomlreader


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
            template = ''
            if 'template' in data:
                template = data['template']
            response['DATA'] = repos.exec(data['name'], template)

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

    elif path == '/saverepoconfig':
        if response['AUTHED']:
            response['OK'] = True
            cfg = json.loads(data['config'])
            repos.setConfig(data['name'], data['template'], cfg)

    elif path == '/deleterepoconfig':
        if response['AUTHED']:
            response['OK'] = True
            repos.deleteConfig(data['name'], data['template'])

    elif path == '/stdin':
        if response['AUTHED']:
            response['OK'] = True
            message = ''
            if 'message' in data:
                message = data['message']
            repos.stdIn(data['name'], message)


    elif path == '/createapp':
        if response['AUTHED']:
            response['OK'] = True
            
            if data['standalone'] == 'true':
                 data['standalone'] = True
            else:
                data['standalone'] = False
                
            tomldata = {
                'app': {
                    'ident': data['ident'],
                    'name': data['name'],
                    'version': '0.1',
                    'launcher': 'init.py',
                    'language': 'python',
                    'args': '',
                    'standalone': data['standalone'],
                },

                'requirements': {
                    'modules': [],
                    'pytainerversion': '0.1',
                },

                'info': {
                    'author': data['author'],
                    'website': '',
                }

            }
            os.mkdir(config.getStr('REPOS','ROOT', vars.path + '/repos/' + data['ident']))
            #with open('new_toml_file.toml', 'w') as f:
            
            with open(config.getStr('REPOS','ROOT', vars.path + '/repos/' + data['ident']) + '/pytainer.toml', 'w', encoding='utf-8') as f:
                new_toml_string = tomlreader.dump(tomldata, f)

            with open(config.getStr('REPOS','ROOT', vars.path + '/repos/' + data['ident']) + '/init.py', 'w', encoding='utf-8') as f:
                #!/usr/bin/python
                f.write('#!/usr/bin/python\n\n')   
                f.write('# Required imports for pyTainer\n')   
                f.write('import sys\n')   
                f.write('import pathlib\n')
                f.write('sys.path.insert(0, str(pathlib.Path(__file__).parent.resolve()) + \'/../../ipc\')\n')   
                f.write('import pytaineripc\n\n')   
                f.write('# Your code here\n')   
                f.write('config = pytaineripc.getConfig(\''+data['ident']+'\')\n\n')   
                f.write('print("pyTainer Default Standalone Template")\n')   
                





    else:
        response['ERR'] = 'Unknown Method'

    request.reply(json.dumps(response))
    