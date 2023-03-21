import hashlib

def sha256(text):
    m = hashlib.sha256()
    binSrc = text.encode('ascii')
    m.update(binSrc)
    return str(m.hexdigest())