import db
import cryptolib
import logger
import random

def create(username, password, permissions):   
    newloginkey = cryptolib.sha256(str(username) + str(random.randint(100000,999999)))
    newuser = {
        'username': username,
        'password': cryptolib.sha256(password),
        'permissions': permissions,
        'loginkey': newloginkey,
    }
    id = db.insert('users', newuser)
    logger.info('New user created. ID: ' + str(id))

def authenticate(username, password):
    results = db.get('SELECT * FROM users WHERE username="'+db.esc(username)+'"')
    if len(results) > 0:
        if results[0]['password'] == cryptolib.sha256(password):
            newloginkey = cryptolib.sha256(str(username) + str(random.randint(100000,999999)))
            db.ex('UPDATE users SET loginkey="'+newloginkey+'" WHERE id=' + str(results[0]['id']))
            results[0]['loginkey'] = newloginkey
            return results[0]
        else:
            return False
    else:
        return False
    
def authenticatelk(loginkey):
    results = db.get('SELECT * FROM users WHERE loginkey="'+db.esc(loginkey)+'"')
    if len(results) > 0:
        return results[0]
    else:
        return False    