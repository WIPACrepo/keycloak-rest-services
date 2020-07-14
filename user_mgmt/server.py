"""
Server for user management
"""

import os
import logging

from tornado.web import RequestHandler, StaticFileHandler, HTTPError
from rest_tools.server import RestServer, RestHandlerSetup, from_environment
import motor.motor_asyncio

import krs.token

from .insts import (Experiments, Institutions, InstApprovals,
                    InstApprovalsActionApprove, InstApprovalsActionDeny)
from .groups import (MultiGroups, Group, GroupUser, GroupApprovals,
                     GroupApprovalsActionApprove, GroupApprovalsActionDeny)


class Error(RequestHandler):
    def prepare(self):
        raise HTTPError(404, 'invalid api route')

def create_server():
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')

    class Main(StaticFileHandler):
        @classmethod
        def get_absolute_path(cls, root: str, path: str) -> str:
            return os.path.join(static_path, 'index.html')


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
    logging.info(f'DB: {config["DB_URL"]}')
    db = motor.motor_asyncio.AsyncIOMotorClient(config['DB_URL'])
    db_name = config['DB_URL'].split('/')[-1]
    logging.info(f'DB name: {db_name}')
    kwargs['db'] = db[db_name]

    kwargs['token'] = krs.token.get_token()

    server = RestServer(static_path=static_path, debug=config['DEBUG'])

    server.add_route('/api/experiments', Experiments, kwargs)
    server.add_route('/api/experiments/(?P<experiment>\w+)/institutions', Institutions, kwargs)

    server.add_route('/api/inst_approvals', InstApprovals, kwargs)
    server.add_route(r'/api/inst_approvals/(?P<approval_id>\w+)/actions/approve', InstApprovalsActionApprove, kwargs)
    server.add_route(r'/api/inst_approvals/(?P<approval_id>\w+)/actions/deny', InstApprovalsActionDeny, kwargs)

    server.add_route('/api/groups', MultiGroups, kwargs)
    server.add_route(r'/api/groups/(?P<group>\w+)', Group, kwargs)
    server.add_route(r'/api/groups/(?P<group>\w+)/(?P<username>\w+)', GroupUser, kwargs)

    server.add_route('/api/group_approvals', GroupApprovals, kwargs)
    server.add_route(r'/api/group_approvals/(?P<approval_id>\w+)/actions/approve', GroupApprovalsActionApprove, kwargs)
    server.add_route(r'/api/group_approvals/(?P<approval_id>\w+)/actions/deny', GroupApprovalsActionDeny, kwargs)

    server.add_route(r'/api/(.*)', Error)
    server.add_route(r'/(.*)', Main, {'path': ''})

    server.startup(address=config['HOST'], port=config['PORT'])

    return server
