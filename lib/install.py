import db
import logger
import users

def fresh():
    logger.info("Fresh Database Installation...")
    db.clear()
    db.ex('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(99) NOT NULL UNIQUE,
            password VARCHAR(99) NOT NULL,
            permissions INT(11) NOT NULL DEFAULT '0'
        );
    ''')

    print("Enter Admin Username:")
    username = input()
    print("Enter Admin Password:")
    password = input()

    users.create(username,password,123)

