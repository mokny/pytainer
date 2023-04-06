import json
import users
import cryptolib
import repos
import logger
import config
import os
import psutil
import vars
import urllib.request
import pytaineripcserver
import functools
import triggers
import pip

try:
    import toml as tomlreader
except:
    import tomllib as tomlreader

def get_directory_structure(rootdir):
    dir = {}
    rootdir = rootdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(rootdir):
        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)
        parent = functools.reduce(dict.get, folders[:-1], dir)
        parent[folders[-1]] = subdir
    return dir

def apiCall(request, path, data):
    response = {
        'OK': False,
        'AUTHED': False,
        'METHOD': path,
    }

    if request.sessionGet('user'):
        response['AUTHED'] = True

    if path == '/authlk':
        if 'loginkey' in data:
            result = users.authenticatelk(data['loginkey'])
            if (result):
                request.sessionWrite('user', result)
                response['OK'] = True
                response['AUTHED'] = True
                response['USERNAME'] = result['username']
                response['LK'] = result['loginkey']
            else:
                request.sessionWrite('user', False)
                response['OK'] = False
                response['ERR'] = 'Invalid login'
                response['AUTHED'] = False
                response['LK'] = False
        else:    
            request.sessionWrite('user', False)
            response['OK'] = False
            response['ERR'] = 'Invalid login'
            response['AUTHED'] = False
            response['LK'] = False


    if path == '/auth':
        if 'username' in data and 'password' in data:
            result = users.authenticate(data['username'], data['password'])
            if (result):
                request.sessionWrite('user', result)
                response['OK'] = True
                response['AUTHED'] = True
                response['USERNAME'] = result['username']
                response['LK'] = result['loginkey']
            else:
                request.sessionWrite('user', False)
                response['OK'] = False
                response['ERR'] = 'Invalid login'
                response['AUTHED'] = False
                response['LK'] = False
        else:    
            request.sessionWrite('user', False)
            response['OK'] = False
            response['ERR'] = 'Invalid login'
            response['AUTHED'] = False
            response['LK'] = False


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

    elif path == '/restartrepo':
        if response['AUTHED']:
            response['OK'] = True
            response['SUCCESS'] = repos.stop(data['name'])
            template = ''
            if 'template' in data:
                template = data['template']
            response['DATA'] = repos.exec(data['name'], template)


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
            if repos.download(data['url']):
                response['OK'] = True
            else:
                response['OK'] = False
                response['ERR'] = 'Repository could not be downloaded'

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
                'repos': repos.getAllPerformance(),
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

            with open(config.getStr('REPOS','ROOT', vars.path + '/repos/' + data['ident']) + '/setup.pytainer', 'w', encoding='utf-8') as f:
                f.write('# Sample setup file\n')
                f.write('# Read the docs for more information\n')

            if data['standalone']:
                with open(config.getStr('REPOS','ROOT', vars.path + '/repos/' + data['ident']) + '/init.py', 'w', encoding='utf-8') as f:
                    #!/usr/bin/python
                    f.write('#!/usr/bin/python\n\n')   
                    f.write('# Required imports for pyTainer\n')   
                    f.write('import sys, pathlib\n')   
                    f.write('sys.path.insert(0, str(pathlib.Path(__file__).parent.resolve()) + \'/../../ipc\')\n')   
                    f.write('import pytaineripc\n\n')   
                    f.write('# Your code here - All below is optional\n\n')   
                    f.write('def pytainerNotificationHandler(data):\n')   
                    f.write('   print("Notification received:" + str(data))\n\n')   
                    f.write('def pytainerEventHandler(data):\n')   
                    f.write('   print("Event received:" + str(data))\n\n')   
                    f.write('# Initialize the IPC interface to receive notifications and events\n')   
                    f.write('pytaineripc.init(__file__, pytainerNotificationHandler, pytainerEventHandler)\n\n')   
                    f.write('# Get the config from the UI\n')   
                    f.write('config = pytaineripc.getConfig()\n\n')   
                    f.write('print("pyTainer Default Standalone Template. Edit '+config.getStr('REPOS','ROOT', vars.path + '/repos/' + data['ident']) + '/init.py' + ' to code your own app.")\n')   
            else:                
                with open(config.getStr('REPOS','ROOT', vars.path + '/repos/' + data['ident']) + '/init.py', 'w', encoding='utf-8') as f:
                    #!/usr/bin/python
                    f.write('import sys, pathlib\n')   
                    f.write('import pytaineripc\n\n')   
                    f.write('# Your code here\n')   
                    f.write('def pytainer_init(app):\n')   
                    f.write('   config = app.config\n')   
                    f.write('   print("App initialized!")\n')   
                    f.write('   pass\n\n')   
                    f.write('def pytainer_stop(app):\n')   
                    f.write('   pass\n\n')   
                    f.write('print("pyTainer Default Module Template. Edit '+config.getStr('REPOS','ROOT', vars.path + '/repos/' + data['ident']) + '/init.py' + ' to code your own app.")\n')   
            repos.scanFolder()

    elif path == '/gettemplates':
        if response['AUTHED']:
            try:
                template = urllib.request.urlopen(config.getStr('REPOS','TEMPLATEURL', 'https://raw.githubusercontent.com/mokny/pytainer/main/misc/templates/common.toml'), timeout=10)
                data = template.read()    
                text = data.decode('utf-8')
                response['OK'] = True
                response['DATA'] = tomlreader.loads(text)
            except Exception as ex:
                response['OK'] = False
                response['DATA'] = False
                response['ERR'] = 'Failed to load template ' + str(ex)

    elif path == '/raiseevent':
        if response['AUTHED']:
            response['OK'] = True
            type = ''
            payload = False
            if 'type' in data:
                type = data['type']
            if 'payload' in data:
                payload = data['payload']
            pytaineripcserver.raiseEvent(type, payload)

    elif path == '/getdirectory':
        if response['AUTHED']:
            response['OK'] = True
            dir = get_directory_structure(repos.repos[data['name']]['path'])
            for x in dir:
                response['DATA'] = dir[x]
                break

    elif path == '/getfilecontent':
        if response['AUTHED']:
            if not '..' in data['path']:
                basepath = repos.repos[data['name']]['path']
                if os.path.isfile(basepath + '/' + data['path']):
                    with open(basepath + '/' + data['path'], 'r') as file:
                        response['OK'] = True
                        response['DATA'] = file.read()

    elif path == '/savefilecontent':
        if response['AUTHED']:
            if not '..' in data['path']:
                basepath = repos.repos[data['name']]['path']
                if os.path.isfile(basepath + '/' + data['path']):
                    with open(basepath + '/' + data['path'], 'w') as file:
                        response['OK'] = True
                        file.write(str(data['content']))

    elif path == '/createfolder':
        if response['AUTHED']:
            if not '..' in data['path']:
                basepath = repos.repos[data['name']]['path']
                os.mkdir(basepath + '/' + data['path'])

    elif path == '/createfile':
        if response['AUTHED']:
            if not '..' in data['path']:
                basepath = repos.repos[data['name']]['path']
                with open(basepath + '/' + data['path'], 'w', encoding='utf-8') as f:
                    f.write('')   

    elif path == '/getpackages':
        if response['AUTHED']:
            response['OK'] = True
            dir = get_directory_structure(vars.path + '/packages')
            for x in dir:
                response['DATA'] = dir[x]
                break

    elif path == '/installpackage':
        if response['AUTHED']:
            response['OK'] = repos.unpackage(vars.path + '/packages/' + data['filename'])
            
    elif path == '/deletepackage':
        if response['AUTHED']:
            try:
                os.remove(vars.path + '/packages/' + data['filename'])
                response['OK'] = True
            except:
                response['OK'] = False
            
    elif path == '/createpackage':
        if response['AUTHED']:
            response['OK'] = repos.package(data['name'])

    elif path == '/createtrigger':
        if response['AUTHED']:
            response['OK'] = triggers.create(data)
            

    elif path == '/gettriggers':
        if response['AUTHED']:
            response['OK'] = True
            response['DATA'] = triggers.triggers
            
    elif path == '/removetrigger':
        if response['AUTHED']:
            response['OK'] = triggers.removetrigger(data['method'], data['ident'])

    elif path == '/pipinstall':
        if response['AUTHED']:
            response['OK'] = pip.install(data['package'])

    elif path == '/pipuninstall':
        if response['AUTHED']:
            response['OK'] = pip.remove(data['package'])


    else:
        response['ERR'] = 'Unknown Method'

    request.reply(json.dumps(response))
    