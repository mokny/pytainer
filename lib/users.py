import db
import cryptolib
import logger

def create(username, password, permissions):    
    newuser = {
        'username': username,
        'password': cryptolib.sha256(password),
        'permissions': permissions
    }
    id = db.insert('users', newuser)
    logger.info('New user created. ID: ' + str(id))

def authenticate(username, password):
    results = db.get('SELECT * FROM users WHERE username="'+db.esc(username)+'"')
    if len(results) > 0:
        if results[0]['password'] == cryptolib.sha256(password):
            return results[0]
        else:
            return False
    else:
        return False