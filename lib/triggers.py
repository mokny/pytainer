import vars
import repos
import re
import logger
import pytaineripcserver
import db
import os

try:
    import toml as tomlreader
except:
    import tomllib as tomlreader

triggers = {
    'consoleline': {}
}

def reloadTriggers():
    global triggers
    if os.path.isfile(vars.path + '/tmp/triggers.toml'):
        triggers = tomlreader.load(vars.path + '/tmp/triggers.toml')
        

def create(data):
    triggers[data['condition_method']][data['trigger_ident']] = {
        'ident': data['trigger_ident'],
        'app': data['condition_app'],
        'type': data['condition_type'],
        'value': data['condition_value'],
        'action': {
            'type': data['action_type'],
            'value': data['action_value'],
            'payload': data['action_payload'],
        }
    }
    

    with open(vars.path + '/tmp/triggers.toml', 'w') as toml_file:
        new_toml_string = tomlreader.dump(triggers, toml_file)    
    return True

def consoleline(app, text):
    # Console Output Triggers
    for key in triggers['consoleline']:
        if triggers['consoleline'][key]['app'] == app or triggers['consoleline'][key]['app'] == '*':
            
            # Contains
            if triggers['consoleline'][key]['type'] == 'contains':
                if triggers['consoleline'][key]['value'] in text or triggers['consoleline'][key]['value'] == '*':
                    _execAction('consoleline', key)

            # RegEx
            if triggers['consoleline'][key]['type'] == 'regex':
                if re.search(triggers['consoleline'][key]['value'], text.rstrip()):
                    _execAction('consoleline', key)


def _execAction(method, triggerident):
    trigger = triggers[method][triggerident]

    #Run App
    if trigger['action']['type'] == 'runapp':
        repos.exec(trigger['action']['value'], '')

    #Logger Info
    if trigger['action']['type'] == 'logger.info':
        logger.info(trigger['action']['value'])

    #Logger Warning
    if trigger['action']['type'] == 'logger.warning':
        logger.warning(trigger['action']['value'])

    #Logger Error
    if trigger['action']['type'] == 'logger.error':
        logger.error(trigger['action']['value'])

    #Raise Event
    if trigger['action']['type'] == 'raiseevent':
        pytaineripcserver.raiseEvent(trigger['action']['value'], trigger['action']['payload'])

