import vars
import db
import config
import os
import importlib
import sys
import logger
import json
import git
import shutil
import threading
import copy
import subprocess
import contextlib, io
from multiprocessing import Process
import wss
import uuid
import traceback
import pip
import triggers
import shutil

try:
    import toml as tomlreader
except:
    import tomllib as tomlreader


repos = {}
repoinfos = {}
threads = {}


def readManifest(path):
    return tomlreader.load(path)

def scanFolder():
    global repos, repoinfos
    repos = {}
    repoinfos = {}    
    folders = [f.path for f in os.scandir(config.getStr('REPOS','ROOT', vars.path + '/repos')) if f.is_dir()]
    for folder in folders:
        reloadRepo(folder)

def reloadRepo(folder):
    if os.path.isfile(folder + '/pytainer.toml'):
        moduleclearname = os.path.basename(os.path.normpath(folder))
        modulename = moduleclearname
        modulepath = folder + '/init.py'
        tomlpath = folder + '/pytainer.toml'
        
        cfg = readManifest(tomlpath)

        modulename = cfg['app']['ident']

        repos[modulename] = {
            'name': modulename,
            'clearname': moduleclearname,
            'path': folder,
            'launcher': folder + '/' + cfg['app']['launcher'],
            'config': cfg,
            'module': False,
            'spec': False,
        }
        
        repoinfos[modulename] = {
            'name': modulename,
            'clearname': moduleclearname,
            'path': folder,
            'launcher': folder + '/' + cfg['app']['launcher'],
            'config': cfg,
        }

        repoinfos[modulename] = copy.copy(repos[modulename])
        del repoinfos[modulename]['module']
        del repoinfos[modulename]['spec']
        
        if cfg['app']['standalone']:
            logger.info('Standalone ' + repos[modulename]['config']['app']['name'] + ' by ' + repos[modulename]['config']['info']['author'])
        else:
            logger.info('Loading App ' + repos[modulename]['config']['app']['name'] + ' by ' + repos[modulename]['config']['info']['author'])

            repos[modulename]['spec'] = importlib.util.spec_from_file_location(modulename, repos[modulename]['launcher'])
            repos[modulename]['module'] = importlib.util.module_from_spec(repos[modulename]['spec'])
            sys.modules[modulename] = repos[modulename]['module']




def exec(modulename, template):
    if not isRunning(modulename):
        if modulename in repos:
            fn = package(modulename)
            unpackage(fn)

            reloadRepo(repos[modulename]['path'])
            setActiveConfig(modulename, template)
            threads[modulename] = RepoThread()
            threads[modulename].setRepo(repos[modulename])

            customconfig = copy.copy(getActiveConfig(modulename))

            if customconfig:
                for key in threads[modulename].config:
                    if key in customconfig and key in threads[modulename].config:
                        threads[modulename].config[key] = customconfig[key]

            threads[modulename].start()
            return True
        else:
            logger.error('Module ' + modulename + ' not found.')
            return False
    return False

def stop(modulename):
    if isRunning(modulename):
        if modulename in repos:
            if modulename in threads:
                try:
                    threads[modulename].stop()
                    return True
                except:
                    logger.error('Repo ' + modulename + ' does not support stopping')
                    return False
            else:
                logger.error('Repo ' + modulename + ' is not running')
                return False
        else:
            logger.error('Module ' + modulename + ' not found.')
            return False
    else:
        return False

def package(modulename):
    logger.info("Packaging " + modulename)
    try:
        if modulename in repos:
            shutil.make_archive(vars.path + '/tmp/' + modulename, 'zip', repos[modulename]['path'])
            logger.info('Package created successfully: ' + vars.path + '/tmp/' + modulename + '.zip')
            return vars.path + '/tmp/' + modulename + '.zip'
        else:
            logger.error('Packaging error: ' + modulename + ' not found.')
            return False
    except Exception as ex:
        logger.error('Packaging error: ' + modulename + ' could not be packed. Reason: ' +  str(ex))
        return False
    
def unpackage(filename):
    try:
        logger.info("Installing package " + filename)
        dir = vars.path + '/tmp/' + str(uuid.uuid4())
        shutil.unpack_archive(filename, dir)
        info = getrawinfo(dir)
        if info:
            logger.info("Package name: " + info['app']['ident'])
            if not info['app']['ident'] in repos:
                shutil.copytree(dir, config.getStr('REPOS','ROOT', vars.path + '/repos') + '/' + info['app']['ident'], dirs_exist_ok=True)
                logger.info("Package installed successfully")
                shutil.rmtree(dir, True)
                return True
            else:
                logger.error("Package already exists.")
                shutil.rmtree(dir, True)
                return False
        shutil.rmtree(dir, True)
        return False
    except Exception as ex:
        shutil.rmtree(dir, True)
        logger.info(filename + ' could not be installed: ' + str(ex))
        return False
    
def getrawinfo(path):
    try:
        if os.path.isfile(path + '/pytainer.toml'):
            cfg = readManifest(path + '/pytainer.toml')
            return cfg
        return False
    except:
        return False
    
def getList():
    ret = {}
    for repo in repoinfos:
        ret[repo] = repoinfos[repo]
        ret[repo]['running'] = isRunning(repo)
    return ret

def getDetails(name):
    if name in repoinfos:
        ret = repoinfos[name]
        ret['running'] = isRunning(name)
        ret['customconfigs'] = loadConfigs(name)
        ret['activeconfig'] = getActiveConfigTemplateName(name)
        return ret
    return False

def loadConfigs(name):
    ret = {}
    if name in repoinfos:
        details = repoinfos[name]
        if 'config' in details['config']:
            defaults = details['config']['config']
            data = db.get('SELECT * FROM repoconfig WHERE ident="' + name + '"')
            for row in data:
                custom = json.loads(db.unesc(row['config']))
                for key in copy.copy(custom):
                    if key in defaults:
                        if defaults[key]['type'] == 'int':
                            if key in custom:
                                custom[key] = int(custom[key])
                        if defaults[key]['type'] == 'string':
                            if key in custom:
                                custom[key] = str(custom[key])
                        if defaults[key]['type'] == 'float':
                            if key in custom:
                                custom[key] = float(custom[key].replace(',','.'))

                        ret[row['template']] = custom
    return ret

def setConfig(name, template, config):
    db.ex('DELETE FROM repoconfig WHERE ident="'+name+'" AND template="'+template+'"')
    insert = {
        'ident': name,
        'template': template,
        'config': json.dumps(config),
    }
    id = db.insert('repoconfig', insert)
    
    setActiveConfig(name, template)
    

def setActiveConfig(name, template):
    if not template == '':
        db.ex('DELETE FROM lastusedconfigs WHERE ident="'+name+'"')
        insert = {
            'ident': name,
            'template': template,
        }
        id = db.insert('lastusedconfigs', insert)

def deleteConfig(name, template):
    db.ex('DELETE FROM repoconfig WHERE ident="'+name+'" AND template="'+template+'"')

def getActiveConfig(name):
    s = db.get('SELECT * FROM lastusedconfigs WHERE ident="'+name+'"')
    if len(s) > 0:
        configs = loadConfigs(name)
        lastusedtemplate = s[0]['template']
        if lastusedtemplate in configs:
            return configs[lastusedtemplate]
    else:
        return False
    return False

def getActiveConfigTemplateName(name):
    s = db.get('SELECT * FROM lastusedconfigs WHERE ident="'+name+'"')
    if len(s) > 0:
        return s[0]['template']
    else:
        return ''

def getJSONList():
    return json.dumps(repoinfos)

def remove(name):
    if not isRunning(name):
        if name in repos:
            path = repos[name]['path']
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path, True)
                    logger.info('Repo ' + name + ' removed.')
                    del repos[name]
                    del repoinfos[name]
                    scanFolder()
                    return True
                except Exception as ex:
                    logger.error('Repo ' + name + ' could not be removed. Error:' + str(ex))
                    return False
            else:
                logger.error('Repo path ' + path + ' not found.')
                return False
        else:
            logger.error('Repo ' + name + ' not found.')
            return False
    else:
        logger.error('Repo ' + name + ' is running and can not be removed!')
        return False

def gitfetch(url):
    foldername = str(uuid.uuid4())
    url = url.replace('://','://:@')
    logger.info('Fetching GIT from url ' + url)
    try:
        git.Repo.clone_from(url, config.getStr('REPOS','ROOT', vars.path + '/repos') + '/' + foldername)
        scanFolder()
        return True
    except Exception as ex:
        logger.error("Could not fetch Repository from " + url + " Error: " + str(ex))
        return False

def isRunning(modulename):
    if modulename in threads:
        if threads[modulename].running:
            return True
    return False

def isAvailable(modulename):
    if modulename in repos:
        return True
    return False

def addOutput(modulename, message):
    if modulename in threads:
        threads[modulename].output.append(message)
        if len(threads[modulename].output) > config.getInt('LOGGING','CONSOLELINES', 100):
            threads[modulename].output.pop(0)
        m = {
            'R': modulename,
            'M': message
        }
        wss.sendAll('CONSOLE', m)

def getOutput(modulename):
    if modulename in threads:
        return threads[modulename].output
    return []

def getAllOutput():
    ret = {}
    for modulename in threads:
        ret[modulename] = getOutput(modulename)
    return ret

def sendOutput(client):
    outputs = getAllOutput()
    for module in outputs:
        for data in outputs[module]:
            m = {
                'R': module,
                'M': data
            }
            wss.send(client,'CONSOLE', m)

def stdIn(modulename, text):
    if modulename in threads:
        threads[modulename].sendStdIn(text)
   

class RepoThread(threading.Thread):
    def __init__(self,  *args, **kwargs):
        super(RepoThread, self).__init__(*args, **kwargs)
        self.setName('RepoThread')
        self._stop_event = threading.Event()
        self.interval = 10 
        self.repo = False
        self.running = False
        self.process = False
        self.stdout = False
        self.stdin = False
        self.config = {}
        self.output = []

    def setRepo(self,repo):
        self.repo = repo
        if 'config' in self.repo['config']:
            for key in self.repo['config']['config']:
                if 'value' in self.repo['config']['config'][key]:
                    self.config[key] = self.repo['config']['config'][key]['value']
        self.setName(self.repo['config']['app']['ident'])

    def getOutput(self):
        return self.output

    def sendStdIn(self, text):
        if self.running:
            print(text, file=self.process.stdin, flush=True)

    def run(self):
        #check pytainer version
        if vars.versionCompare(vars.pytainerversion, self.repo['config']['requirements']['pytainerversion']) < 0:
            logger.error(self.repo['config']['app']['name'] + ' requires pyTainer Version ' + self.repo['config']['requirements']['pytainerversion'] + ' - Exiting.')
            return

        #install modules if neccessary
        for mod in self.repo['config']['requirements']['modules']:
            if not pip.exists(mod):
                logger.error(self.repo['config']['app']['name'] + " required module " + mod + ', which is missing.')
                return
            
        with open(vars.path+'/tmp/'+self.repo['config']['app']['ident']+'_config.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.config))    

        self.running = True
        wss.sendAll('APPRUN', self.repo['config']['app']['ident'])

        try:
            if self.repo['config']['app']['standalone']:
                cmdparams = []
                if self.repo['config']['app']['language'].strip() != '':
                    cmdparams.append(self.repo['config']['app']['language'].strip())
                    if self.repo['config']['app']['language'].strip().startswith('python'):
                        cmdparams.append('-u')

                cmdparams.append(self.repo['launcher'].strip())
                
                if self.repo['config']['app']['args'].strip() != '':
                    cmdparams.append(self.repo['config']['app']['args'].strip())

                try:
                    self.process = subprocess.Popen(cmdparams, stdout = subprocess.PIPE, stdin = subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                    while self.running:
                        line = self.process.stdout.readline()
                        if not line:
                            break
                        print(line)
                    err = self.process.stderr.read()                
                    if err:
                        print('ERROR: ' + str(err))

                except Exception as ex:
                    logger.error('Standalone app ' + self.repo['name'] + ' threw error: ' + str(ex))
                logger.info(self.repo['config']['app']['name'] + ' ended.')
            else:
                try:
                    logger.info('Executing Repo ' + self.repo['name'])
                    self.repo['spec'].loader.exec_module(self.repo['module'])
                    try:
                        self.repo['module'].pytainer_init(self)
                        pass
                    except Exception as ex:
                        print(ex)
                        pass
                except Exception as ex:
                    err = traceback.format_exc()
                    logger.error('Module ' + self.repo['name'] + ' threw error: ' + str(ex))
                    logger.error(str(err))

        except Exception as ex:
            logger.error('APP could not be started! Reason:' + str(ex))

        self.running = False
        wss.sendAll('APPSTOP', self.repo['config']['app']['ident'])

    def stop(self):
        if self.process:
            self.running = False
            self.process.terminate()
        else:
            try:
                self.repo['module'].pytainer_stop(self)
                logger.info(self.repo['config']['app']['name'] + ' stop requested.')
            except:
                logger.info(self.repo['config']['app']['name'] + ' does not support stopping. Public function pytainer_stop(foo) missing.')
                pass
        self._stop_event.set()
        #wss.sendAll('APPSTOP', self.repo['config']['app']['ident'])
    
    def stopped(self):
            return self._stop_event.is_set()

