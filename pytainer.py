#!/usr/bin/python

#Default modules
import sys
import os

#Custom modules
sys.path.insert(0, './lib')
import logger
import config
import db
import pytainerserver
import install
import shellib

logger.setLevel(logger.LEVEL_ERROR)

config.load('config.ini')


# Commandline Options
def optionHandler(opt, arg):
    if opt == "-h":
        print('#### pyTainer ####')
        print('Installation')
        print(' -i fresh        - Clean install')
        print(' -l              - Log everything')
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

shellib.addOption('i', True) # Option Install
shellib.addOption('h', False) # Option Help
shellib.addOption('l', False) # Option Help
shellib.addOption('q', False) # Option Help
shellib.getOptions(optionHandler)

if not os.path.isfile(config.getStr('DATABASE','FILENAME','database.sqlite')):    
    logger.error("Database not found. Make sure your installed pyTainer with the command -i fresh")
    exit()

db.open(config.getStr('DATABASE','FILENAME','database.sqlite'))


logger.out('pyTainer Starting up')



logger.info(db.get('SELECT * FROM users'))
pytainerserver.listen(config.getStr('WEBSERVER','HOST','0.0.0.0'), config.getInt('WEBSERVER','PORT',6880))
