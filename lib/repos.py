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
    folders = [f.path for f in os.scandir(config.getStr('REPOS','ROOT', vars.path + '/repos')) if f.is_dir()]
    for folder in folders:
        if os.path.isfile(folder + '/pytainer.toml'):
            moduleclearname = os.path.basename(os.path.normpath(folder))
            modulename = moduleclearname
            modulepath = folder + '/init.py'
            tomlpath = folder + '/pytainer.toml'
            
            cfg = readManifest(tomlpath)
            print(cfg)

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


def exec(modulename):
    if modulename in repos:
        threads[modulename] = RepoThread()
        threads[modulename].setRepo(repos[modulename])
        threads[modulename].start()
        return True
    else:
        logger.error('Module ' + modulename + ' not found.')
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
    
def getList():
    ret = {}
    for repo in repoinfos:
        ret[repo] = repoinfos[repo]
        ret[repo]['running'] = isRunning(repo)
    return ret

def getJSONList():
    return json.dumps(repoinfos)

def remove(name):
    if os.path.isdir(config.getStr('REPOS','ROOT', vars.path + '/repos') + '/' + name):
        try:
            shutil.rmtree(config.getStr('REPOS','ROOT', vars.path + '/repos')+ '/' + name, True)
            logger.info('Repo ' + name + ' removed.')
        except Exception as ex:
            logger.error('Repo ' + name + ' could not be removed. Error:' + str(ex))
    else:
        logger.error('Repo ' + name + ' not found.')

def gitfetch(name, url):
    logger.info('Fetching GIT from url ' + url)
    try:
        git.Repo.clone_from(url, config.getStr('REPOS','ROOT', vars.path + '/repos') + '/' + name)
        return True
    except Exception as ex:
        logger.error("Could not fetch Repository from " + url + " Error: " + str(ex))
        return False

def isRunning(modulename):
    if modulename in threads:
        if threads[modulename].running:
            return True
    return False

def addOutput(modulename, message):
    if modulename in threads:
        threads[modulename].output.append(message)
        m = {
            'R': modulename,
            'M': message
        }
        wss.sendAll('CONSOLE', m)

def getOutput(modulename):
    if modulename in threads:
        return threads[modulename].output
    return []
   

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
        self.output = []

    def setRepo(self,repo):
        self.repo = repo
        self.setName(self.repo['config']['app']['ident'])


    def getOutput(self):
        return self.output

    def run(self):
        self.running = True
        wss.sendAll('APPRUN', self.repo['config']['app']['ident'])

        if self.repo['config']['app']['standalone']:
            self.process = subprocess.Popen(['python', '-u', self.repo['launcher']], stdout = subprocess.PIPE)
            while self.running:
                line = self.process.stdout.readline().rstrip().decode("UTF-8")
                if not line:
                    break
                print(line)
            logger.info(self.repo['config']['app']['name'] + ' ended.')
        else:
            try:
                logger.info('Executing Repo ' + self.repo['name'])
                self.repo['spec'].loader.exec_module(self.repo['module'])
                try:
                    self.repo['module'].pytainer_init(self)
                    pass
                except:
                    pass
            except Exception as ex:
                logger.error('Module ' + self.repo['name'] + ' threw error: ' + str(ex))
        self.running = False
        wss.sendAll('APPSTOP', self.repo['config']['app']['ident'])

    def stop(self):
        if self.process:
            self.running = False
            self.process.terminate()
        else:
            try:
                self.repo['module'].pytainer_stop(self)
            except:
                pass
        self._stop_event.set()
        wss.sendAll('APPSTOP', self.repo['config']['app']['ident'])
    
    def stopped(self):
            return self._stop_event.is_set()

