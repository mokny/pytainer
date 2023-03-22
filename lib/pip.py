import sys
import subprocess
import importlib

def exists(modulename):
    if importlib.util.find_spec(modulename):
        return True
    else:
        return False

def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def remove(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', package])    