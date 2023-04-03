import datetime
import inspect
import threading
import sys
import repos

LEVEL_ALL = 0
LEVEL_INFO = 1
LEVEL_WARNING = 2
LEVEL_ERROR = 3
LEVEL_NONE = 30000

loggingLevel = 1
history = []

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
        outstr = (str(levelstr[level]) + name + ' ' + str(datetime.datetime.now()) + '> ' + str(text))
        print(outstr)
        history.append(outstr)
        if len(history) > 200:
            history.pop(0)

def getHistory():
    return history


class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
   
    def write(self, message):
        if str(message).strip() != "":
            threadname = str(threading.current_thread().name)
            if threadname == 'MainThread':
                self.terminal.write(message + '\n')
            else:
                self.terminal.write('['+threadname+'] ' + message.rstrip() + '\n')
                repos.addOutput(threadname, message)

    def flush(self):
        pass    

sys.stdout = Logger()