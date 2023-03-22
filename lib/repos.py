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

repos = {}
repoinfos = {}
threads = {}

def scanFolder():
    folders = [f.path for f in os.scandir(config.getStr('REPOS','ROOT', vars.path + '/repos')) if f.is_dir()]
    for folder in folders:
        if os.path.isfile(folder + '/init.py'):
            moduleclearname = os.path.basename(os.path.normpath(folder))
            modulename = moduleclearname
            modulepath = folder + '/init.py'

            repos[modulename] = {
                'name': modulename,
                'clearname': moduleclearname,
                'path': folder,
                'module': False,
                'spec': False,
                'running': False,
            }
            
            repoinfos[modulename] = {
                'name': modulename,
                'clearname': moduleclearname,
                'path': folder,
                'running': False,
            }
            
            logger.info('Loading Repo ' + modulename + ' at ' + modulepath)

            repos[modulename]['spec'] = importlib.util.spec_from_file_location(modulename, modulepath)
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

def getList():
    return repoinfos

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

class RepoThread(threading.Thread):
    def __init__(self,  *args, **kwargs):
        super(RepoThread, self).__init__(*args, **kwargs)
        self.setName('RepoThread')
        self._stop_event = threading.Event()
        self.interval = 10 
        self.repo = False
        self.running = False

    def setRepo(self,repo):
        self.repo = repo

    def run(self):
        self.running = True
        try:
            logger.info('Executing Repo ' + self.repo['name'])
            self.repo['spec'].loader.exec_module(self.repo['module'])
            self.repo['running'] = True
            try:
                self.repo['module'].init()
            except:
                pass
        except Exception as ex:
            logger.error('Module ' + self.repo['name'] + ' threw error: ' + str(ex))
        self.running = False

    def stop(self):
        try:
            self.repo['module'].stop()
        except:
            pass
        self._stop_event.set()
    
    def stopped(self):
            return self._stop_event.is_set()