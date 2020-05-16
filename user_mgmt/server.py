"""
Server for user management
"""

import os

from tornado.web import RequestHandler, StaticFileHandler, HTTPError
from rest_tools.server import RestServer, RestHandlerSetup, from_environment
import motor

from .users import Users, UserDetails, UserGroups
from .group_mgmt import Groups

def create_server():
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')

    class Main(StaticFileHandler):
        @classmethod
        def get_absolute_path(cls, root: str, path: str) -> str:
            return os.path.join(static_path, 'index.html')

    class Error(RequestHandler):
        def prepare(self):
            raise HTTPError(404, 'invalid api route')

    default_config = {
       'HOST': 'localhost',
       'PORT': 8080,
       'DEBUG': False,
       'AUTH_SECRET': None,
       'AUTH_ISSUER': None,
       'AUTH_ALGORITHM': 'RS256',
       'DB_URL': 'mongodb://localhost/keycloak_user_mgmt',
    }
    config = from_environment(default_config)

    rest_config = {
        'debug': config['DEBUG'],
        'auth': {
            'secret': config['AUTH_SECRET'],
            'issuer': config['AUTH_ISSUER'],
            'algorithm': config['AUTH_ALGORITHM'],
        },
    }

    kwargs = RestHandlerSetup(rest_config)
    kwargs['db'] = motor.motor_tornado.MotorClient(config['DB_URL'])

    server = RestServer(static_path=static_path, debug=config['DEBUG'])
    server.add_route('/api/users', Users, kwargs)
    server.add_route(r'/api/users/(?P<user_id>\w+)', UserDetails, kwargs)
    server.add_route(r'/api/users/(?P<user_id>\w+)/groups', UserGroups, kwargs)
    server.add_route('/api/manage-groups', Groups, kwargs)
    server.add_route(r'/api/(.*)', Error)
    server.add_route(r'/(.*)', Main, {'path': ''})
    server.startup(address=config['HOST'], port=config['PORT'])

    return server
