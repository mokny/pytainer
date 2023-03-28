import os
import sqlite3
import logger
import re

con = False

def open(filename):
    global con
    con = sqlite3.connect(filename, check_same_thread=False)
    con.row_factory = dict_factory

def clear():
    logger.info("Clearing Database")
    ex('PRAGMA writable_schema = 1;')
    ex('delete from sqlite_master where type in ("table", "index", "trigger");')
    ex('PRAGMA writable_schema = 0;')
    ex('VACUUM;')

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def clean(strg):
    return re.sub("[^A-Za-z0–9]_-","",strg)

def esc(strg):
    if isinstance(strg,str):
        strg = strg.replace('"','%!%')
        strg = strg.replace("'",'%?%')
    return strg

def unesc(strg):
    if isinstance(strg,str):
        strg = strg.replace('%!%','"')
        strg = strg.replace('%?%',"'")
    return strg


def get(query):
    cur = con.cursor()
    res = cur.execute(query)
    return res.fetchall()   

def ex(query):
    cur = con.cursor()
    cur.execute(query)
    con.commit()

def insert(table, data):
    columns = []
    values = []
    try:
        cur = con.cursor()
        for key in data:
            columns.append(clean(key))
            values.append(str(esc(data[key])))
        s = ("INSERT INTO " + clean(table) + " "
            "(" + ", ".join(columns) + ") VALUES " 
            "('" + "', '".join(values) + "');")  
        
        cur.execute(s)           
        con.commit()
        return cur.lastrowid
    except Exception as e:
        logger.error("DB Insert Error: " + str(e))
        return False
