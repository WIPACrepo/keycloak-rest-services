"""
Server for user management
"""

import os
import logging
from functools import partial

from tornado.web import RequestHandler, StaticFileHandler, HTTPError
from rest_tools.client import RestClient
from rest_tools.server import RestServer, RestHandlerSetup, from_environment
import motor.motor_asyncio

import krs.token

from .insts import (AllExperiments, Experiments, MultiInstitutions, Institution,
                    InstitutionMultiUsers, InstitutionUser,
                    InstApprovals, InstApprovalsActionApprove, InstApprovalsActionDeny)
from .groups import (MultiGroups, Group, GroupUser, GroupApprovals,
                     GroupApprovalsActionApprove, GroupApprovalsActionDeny)


class Error(RequestHandler):
    def prepare(self):
        raise HTTPError(404, 'invalid api route')

class Main(RequestHandler):
    def initialize(self, keycloak_url='', keycloak_realm=''):
        self.keycloak_url = keycloak_url
        self.keycloak_realm = keycloak_realm

    def get(self, *args):
        self.render('index.html', keycloak_url=self.keycloak_url,
                    keycloak_realm=self.keycloak_realm)

def create_server():
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')



    default_config = {
        'HOST': 'localhost',
        'PORT': 8080,
        'DEBUG': False,
        'KEYCLOAK_URL': None,
        'KEYCLOAK_REALM': 'IceCube',
        'KEYCLOAK_CLIENT_ID': 'rest-access',
        'KEYCLOAK_CLIENT_SECRET': None,
        'DB_URL': 'mongodb://localhost/keycloak_user_mgmt',
    }
    config = from_environment(default_config)

    rest_config = {
        'debug': config['DEBUG'],
        'auth': {
            'openid_url': f'{config["KEYCLOAK_URL"]}/auth/realms/{config["KEYCLOAK_REALM"]}'
        }
    }

    kwargs = RestHandlerSetup(rest_config)

    logging.info(f'DB: {config["DB_URL"]}')
    db_url, db_name = config['DB_URL'].rsplit('/',1)
    db = motor.motor_asyncio.AsyncIOMotorClient(db_url)
    logging.info(f'DB name: {db_name}')
    kwargs['db'] = db[db_name]

    logging.info(f'Keycloak client: {config["KEYCLOAK_CLIENT_ID"]}')
    token_func = partial(krs.token.get_token, config["KEYCLOAK_URL"],
        client_id=config['KEYCLOAK_CLIENT_ID'],
        client_secret=config['KEYCLOAK_CLIENT_SECRET'],
    )
    kwargs['krs_client'] = RestClient(
        f'{config["KEYCLOAK_URL"]}/auth/admin/realms/{config["KEYCLOAK_REALM"]}',
        token=token_func,
        timeout=10,
    )

    main_args = {
        'keycloak_url': config['KEYCLOAK_URL'],
        'keycloak_realm': config['KEYCLOAK_REALM'],
    }

    server = RestServer(static_path=static_path, template_path=static_path, debug=config['DEBUG'])

    server.add_route('/api/all-experiments', AllExperiments, kwargs)
    server.add_route('/api/experiments', Experiments, kwargs)
    server.add_route('/api/experiments/(?P<experiment>[\w\-]+)/institutions', MultiInstitutions, kwargs)
    server.add_route('/api/experiments/(?P<experiment>[\w\-]+)/institutions/(?P<institution>[\w\-]+)', Institution, kwargs)
    server.add_route('/api/experiments/(?P<experiment>[\w\-]+)/institutions/(?P<institution>[\w\-]+)/users', InstitutionMultiUsers, kwargs)
    server.add_route('/api/experiments/(?P<experiment>[\w\-]+)/institutions/(?P<institution>[\w\-]+)/users/(?P<username>\w+)', InstitutionUser, kwargs)

    server.add_route('/api/inst_approvals', InstApprovals, kwargs)
    server.add_route(r'/api/inst_approvals/(?P<approval_id>\w+)/actions/approve', InstApprovalsActionApprove, kwargs)
    server.add_route(r'/api/inst_approvals/(?P<approval_id>\w+)/actions/deny', InstApprovalsActionDeny, kwargs)

    server.add_route('/api/groups', MultiGroups, kwargs)
    server.add_route(r'/api/groups/(?P<group_id>[\w\-]+)', Group, kwargs)
    server.add_route(r'/api/groups/(?P<group_id>[\w\-]+)/(?P<username>\w+)', GroupUser, kwargs)

    server.add_route('/api/group_approvals', GroupApprovals, kwargs)
    server.add_route(r'/api/group_approvals/(?P<approval_id>\w+)/actions/approve', GroupApprovalsActionApprove, kwargs)
    server.add_route(r'/api/group_approvals/(?P<approval_id>\w+)/actions/deny', GroupApprovalsActionDeny, kwargs)

    server.add_route(r'/api/(.*)', Error)
    server.add_route(r'/(.*)', Main, main_args)

    server.startup(address=config['HOST'], port=config['PORT'])

    return server
