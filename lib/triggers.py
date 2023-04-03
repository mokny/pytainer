import vars
import repos
import re
triggers = {}

def reloadTriggers():
    triggers['consoleline'] = {
        'asd' : {
            'app': '*',
            'type': 'contains',
            'contains': 'cycle',
            'regmatch': r"^\w+",
            'action': {
                'type': 'runapp',
                'runapp': 'unique_ident'
            }
        }
    }
    pass

def consoleline(app, text):
    # Console Output Triggers
    for key in triggers['consoleline']:
        if triggers['consoleline'][key]['app'] == app or triggers['consoleline'][key]['app'] == '*':
            # Contains
            if triggers['consoleline'][key]['type'] == 'contains':
                if triggers['consoleline'][key]['contains'] in text or triggers['consoleline'][key]['contains'] == '*':
                    if triggers['consoleline'][key]['action']['type'] == 'runapp':
                        repos.exec(triggers['consoleline'][key]['action']['runapp'], '')

            # Regular expression match                        
            #if triggers['consoleline'][key]['type'] == 'regmatch':
            #    if re.findall(triggers['consoleline'][key]['regmatch'], text):
            #        if triggers['consoleline'][key]['action']['type'] == 'runapp':
            #            repos.exec(triggers['consoleline'][key]['action']['runapp'], '')

    pass

reloadTriggers()