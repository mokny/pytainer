import os
import getopt
import sys
import inspect

_mainfile = __file__
_options = {}

if __name__ != '__main__':
    for frame in inspect.stack()[1:]:
        if frame.filename[0] != '<':
            _mainfile = os.path.basename(frame.filename)
            break

def addOption(k, requiresargs):
    _options[k] = requiresargs

def getOptions(handler):
    _cmdstring = ''
    _shellibargs = 'abcdefghijklmnopqrstuvwxyz'
    if not handler is None:
        _shellibargs = ''
        for key in _options:
            if _options[key]:
                _shellibargs += key + ':'
            else:
                _shellibargs += key
    try:
        opts, args = getopt.getopt(sys.argv[1:], _shellibargs, ["bg","kill"])
    except getopt.GetoptError:
        print("Invalid commands. use '" + _mainfile + " -h' for help")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '--bg':
            _runbackground(_cmdstring)
            sys.exit()
        elif opt == '--kill':
            _killallinstances()
            sys.exit()
        else:
            _cmdstring += opt + ' ' + arg + ' '
            if not handler is None:
                handler(opt, arg)


def _runbackground(arguments):
    print("Running " + _mainfile + " in background...")
    os.system('nohup ./' + _mainfile + ' ' + arguments + ' >/dev/null 2>&1 &')
    sys.exit()

def _killallinstances():
    print("Killing all instances of " + _mainfile + " ...")
    os.system('pkill -f ' + _mainfile)

def writePIDFile(path):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
        return True
    except:
        return False

def readPIDFile(path):
    try:
        pid_file = open(path, 'r')
        data = pid_file.read()
        pid_file.close()
        return int(data)
    except:
        return False
    
    
getOptions(None)
