import vars
import repos
import re
import logger
import pytaineripcserver
import db

triggers = {}

def reloadTriggers():
    triggers['consoleline'] = {
        'asd' : {
            'app': 'triggertest',
            'type': 'contains',
            'value': 'cycle',
            'action': {
                'type': 'logger.info',
                'value': 'Cycle found',
                'payload': False,
            }
        },

        'asd2' : {
            'app': '*',
            'type': 'regex',
            'value': 'Do.e',
            'action': {
                'type': 'logger.info',
                'value': 'We have a regex match!',
                'payload': False,
            }
        },

        'asd3' : {
            'app': 'triggertest',
            'type': 'regex',
            'value': 'Do.e',
            'action': {
                'type': 'raiseevent',
                'value': 'TRIGGEREVENT',
                'payload': 'Example Payload',
            }
        }
    }

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


reloadTriggers()