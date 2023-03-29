#!/usr/bin/python
VERSION = '1.1.0'

#Default modules
import sys

if sys.version_info[0] < 3:
    if sys.version_info[1] < 9:
        print('Python 3.9 required')
        exit()

if sys.version_info[1] > 9:
    print('Python 3.9 required')
    exit()

import os
import signal
import time
import pathlib
abspath = str(pathlib.Path(__file__).parent.resolve())

#Custom modules
sys.path.insert(0, abspath + '/ipc')
sys.path.insert(0, abspath + '/lib')

import logger
import pip

if not pip.exists('git'):
    logger.out('Installing GITPYTHON...')
    pip.install('gitpython')
    import git


import config
import db
import pytainerserver
import install
import shellib
import vars
import repos
import wss
import pytaineripc

vars.path = abspath
vars.pid = os.getpid()

logger.setLevel(logger.LEVEL_ERROR)



config.load(vars.path + '/config.ini')


# Commandline Options
def optionHandler(opt, arg):
    if opt == "-h":
        print('#### pyTainer ####')
        print('Installation')
        print(' -i fresh        - Clean install')
        print(' -l              - Log everything')
        print(' -u              - Uninstall')
        exit()
    if opt == "-i":
        db.open(config.getStr('DATABASE','FILENAME','database.sqlite'))
        if arg == "fresh":
            install.fresh()
        else:
            print("Invalid installation option. Use -i fresh")
        exit()
    if opt == '-l':
        logger.setLevel(logger.LEVEL_ALL)
    if opt == '-q':
        logger.setLevel(logger.LEVEL_NONE)
    if opt == '-u':
        install.uninstall()
        exit()

shellib.addOption('i', True) # Option Install
shellib.addOption('h', False) # Option Help
shellib.addOption('l', False) # Option Help
shellib.addOption('q', False) # Option Help
shellib.addOption('u', False) # Option Help
shellib.getOptions(optionHandler)

logger.out('****************************')
logger.out('* pyTainer')
logger.out('****************************')




if not os.path.isfile(config.getStr('DATABASE','FILENAME',vars.path + '/database.sqlite')):    
    logger.error("Database not found. Make sure your installed pyTainer with the command -i fresh")
    exit()

if not os.path.isdir(config.getStr('REPOS','ROOT', vars.path + '/repos')):
    logger.error("The repository root directory does not exist. Consider a fresh install using -i fresh")
    exit()

if not os.access(config.getStr('REPOS','ROOT',vars.path + '/repos'), os.W_OK):
    logger.error("Repository Root is not writable by pyTainer")
    exit()

if not os.path.isdir(vars.path + '/tmp'):
    os.mkdir(vars.path + '/tmp')

# Kill old process
oldpid = shellib.readPIDFile(vars.path + '/tmp/pid.txt')
if oldpid:
    try:
        os.kill(oldpid, signal.SIGINT)
        logger.info("Killed old process... Waiting for complete shutdown")
        time.sleep(5)
    except:
        pass
shellib.writePIDFile(vars.path + '/tmp/pid.txt')

# Open Database Connection
db.open(config.getStr('DATABASE','FILENAME',vars.path + '/database.sqlite'))

repos.scanFolder()
wss.init()
pytaineripc._IPCServerSetVersion(VERSION)
pytaineripc._IPCServerListen(config.getInt('IPC','PORT',6882))
pytainerserver.listen(config.getStr('WEBSERVER','HOST','0.0.0.0'), config.getInt('WEBSERVER','PORT',6880))


