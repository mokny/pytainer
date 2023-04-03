import db
import logger
import users
import config
import os
import shutil
import vars
import pip

def removeDirectories():
    logger.out("Removing old Directories")
    if os.path.isdir(config.getStr('REPOS','ROOT',vars.path + '/repos')):
        shutil.rmtree(vars.path+'/repos', True)

def createDirectories():
    logger.out("Creating Directories")

    #Repository Root
    if not os.path.isdir(config.getStr('REPOS','ROOT',vars.path + '/repos')):
        os.mkdir(config.getStr('REPOS','ROOT', vars.path + '/repos'))

def fresh():
    logger.out("Starting fresh installation of pyTainer")
    logger.out(vars.path)

    #removeDirectories()
    #createDirectories()

    logger.out("Fresh Database Installation...")
    db.clear()

    db.ex('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(99) NOT NULL UNIQUE,
            password VARCHAR(99) NOT NULL,
            loginkey VARCHAR(300) NOT NULL,
            permissions INT(11) NOT NULL DEFAULT '0'
        );
    ''')

    db.ex('''
        CREATE TABLE repoconfig (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ident VARCHAR(99) NOT NULL,
            template VARCHAR(99) NOT NULL,
            config LONGTEXT
        );
    ''')

    db.ex('''
        CREATE TABLE lastusedconfigs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ident VARCHAR(99) NOT NULL UNIQUE,
            template VARCHAR(99) NOT NULL
        );
    ''')


    logger.out("Enter Admin Username:")
    username = input()
    logger.out("Enter Admin Password:")
    password = input()

    users.create(username,password,123)

def uninstall():
    logger.out('Removing GITPYTHON...')
    pip.remove('gitpython')
    
    logger.out('Deleting Database...')
    os.remove(config.getStr('DATABASE','FILENAME',vars.path + '/database.sqlite'))

    logger.out('Removing Directories...')
    removeDirectories()