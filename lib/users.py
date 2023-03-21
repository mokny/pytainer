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