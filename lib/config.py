import os
import configparser
import logger

cfgdata = configparser.ConfigParser()
cfgfilename = False

def load(filename):    
    logger.info("Loading Config")
    if os.path.isfile(filename):    
        try:
            cfgdata.read(filename)
            global cfgfilename 
            cfgfilename = filename
            return True
        except Exception as e:
            logger.error("Config could not be read: " + str(e))
            return False
    else:
        logger.error('Config does not exist')
        return False

def get(section, key, defaultvalue = False):
    section = section.upper()
    key = key.upper()
    if not cfgdata:
        return defaultvalue
    if section in cfgdata:
        if key in cfgdata[section]:
            return cfgdata[section][key]
        else:
            return defaultvalue
    else:
        return defaultvalue

def getInt(section, key, defaultvalue = 0):
    try:
        ret = int(get(section, key, defaultvalue))
        return ret
    except:
        return defaultvalue

def getStr(section, key, defaultvalue = ''):
    try:
        ret = str(get(section, key, defaultvalue))
        return ret
    except:
        return defaultvalue

def set(section, key, value):
    section = section.upper()
    key = key.upper()
    if not section in cfgdata:
        cfgdata.add_section(section)
    cfgdata[section][key] = value

def save(filename = False):
    if not filename:
        if cfgfilename:
            filename = cfgfilename
    if filename:
        with open(filename, 'w') as configfile:
            cfgdata.write(configfile)
        logger.info("Config saved as " + str(filename))
        return True
    else:
        logger.error("Config could not be saved - No filename given.")
        return False