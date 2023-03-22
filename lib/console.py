import inspect

def log(text):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])    
    print(str(text))