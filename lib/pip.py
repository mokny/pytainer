import sys
import subprocess
import importlib

def exists(modulename):
    if importlib.util.find_spec(modulename):
        return True
    else:
        return False

def install(package):
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        return True
    except:
        return False

def remove(package):
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', '--yes', package])
        return True
    except:
        return False
