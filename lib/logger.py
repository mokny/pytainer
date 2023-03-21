import datetime

LEVEL_ALL = 0
LEVEL_INFO = 1
LEVEL_WARNING = 2
LEVEL_ERROR = 3
LEVEL_NONE = 30000

loggingLevel = 1

def setLevel(level):
    global loggingLevel
    loggingLevel = level

def info(text):
    log(LEVEL_INFO, text)

def out(text):
    if loggingLevel == LEVEL_NONE:
        return
    print(text)

def warning(text):
    log(LEVEL_WARNING, text)

def error(text):
    log(LEVEL_ERROR, text)

def log(level, text):
    if (level == LEVEL_NONE):
        return
    
    levelstr = {}
    levelstr[LEVEL_INFO] = 'INFO'
    levelstr[LEVEL_WARNING] = 'WARNING'
    levelstr[LEVEL_ERROR] = 'ERROR'

    if (level >= loggingLevel):
        print(str(levelstr[level]) + ' ' + str(datetime.datetime.now()) + '> ' + str(text))

