import datetime
import inspect

LEVEL_ALL = 0
LEVEL_INFO = 1
LEVEL_WARNING = 2
LEVEL_ERROR = 3
LEVEL_NONE = 30000

loggingLevel = 1

def setLevel(level):
    global loggingLevel
    loggingLevel = level

def out(text):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])    
    name = ""
    if mod.__name__ != '__main__':
        name = '['+mod.__name__+'] '
    if loggingLevel == LEVEL_NONE:
        return
    print(name + text)

def info(text):
    _log(LEVEL_INFO, text)

def warning(text):
    _log(LEVEL_WARNING, text)

def error(text):
    _log(LEVEL_ERROR, text)

def _log(level, text):
    if (level == LEVEL_NONE):
        return
    
    frm = inspect.stack()[2]
    mod = inspect.getmodule(frm[0])    
    name = ' ['+mod.__name__+']'

    levelstr = {}
    levelstr[LEVEL_INFO] = 'INFO'
    levelstr[LEVEL_WARNING] = 'WARNING'
    levelstr[LEVEL_ERROR] = 'ERROR'

    if (level >= loggingLevel):
        print(str(levelstr[level]) + name + ' ' + str(datetime.datetime.now()) + '> ' + str(text))

