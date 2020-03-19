import os

class ConfigRequired:
    pass

def config(defaults):
    ret = {}
    for k in defaults:
        if k in os.environ:
            ret[k] = os.environ[k]
        elif defaults[k] == ConfigRequired:
            raise Exception(f'environment variable {k} is required')
        else:
            ret[k] = defaults[k]
    return ret
