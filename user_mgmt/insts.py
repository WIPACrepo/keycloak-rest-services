"""
Handle user institution-based actions.
"""
import logging
import uuid

import unidecode
from tornado.web import HTTPError
from tornado.escape import json_decode
from rest_tools.server import catch_error, authenticated

import krs.users
import krs.groups

from . import MyHandler

audit_logger = logging.getLogger('audit')


class Experiments(MyHandler):
    @catch_error
    async def get(self):
        """Get a list of experiments"""
        ret = await krs.groups.list_groups(token=self.token)
        exps = set()
        for group in ret:
            val = group.strip('/').split('/')
            if len(val) == 2 and val[0] == 'institutions':
                exps.add(val[1])
        return sorted(exps)


class Institutions(MyHandler):
    @catch_error
    async def get(self, experiment):
        """Get a list of institutions in the experiment"""
        ret = await krs.groups.list_groups(token=self.token)
        insts = set()
        for group in ret:
            val = group.strip('/').split('/')
            if len(val) == 3 and val[0] == 'institutions' and val[1] == experiment:
                insts.add(val[2])
        return sorted(insts)


class InstApprovals(MyHandler):
    @catch_error
    async def post(self):
        """New institution approval request"""
        if self.current_user:
            logging.info('existing user with new institution')
            user = self.auth_data['username']

            req_fields = {
                'experiment': str,
                'institution': str,
            }
            opt_fields = {
                'authorlist': bool,
                'remove_institution': str,
            }
            approval_data = self.json_filter(req_fields, opt_fields)
            approval_data['username'] = user

        else:
            logging.info('new user registration')
            req_fields = {
                'experiment': str,
                'institution': str,
                'first_name': str,
                'last_name': str,
                'email': str,
            }
            opt_fields = {
                'authorlist': bool,
                'author_name': str,
            }
            data = self.json_filter(req_fields, opt_fields)

            user_data = {
                'id': uuid.uuid1().hex,
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'external_email': data['email'],
                'author_name': data['author_name'],
            }
            await self.db.user_registrations.insert_one(user_data)

            approval_data = {
                'experiment': data['experiment'],
                'institution': data['institution'],
                'authorlist': data['authorlist'],
                'newuser': user_data['id'],
            }

        approval_data['id'] = uuid.uuid1().hex
        await self.db.inst_approvals.insert_one(approval_data)

        self.set_status(201)
        self.write({})

    @authenticated
    @catch_error
    async def get(self):
        """Get list of requests a user can approve"""
        insts = await self.get_admin_institutions()
        search = {'$or': {'experiment': exp, 'institution': insts[exp]} for exp in insts}
        ret = await self.db.inst_approvals.find(search)
        self.write(ret)


class InstApprovalsActionApprove(MyHandler):
    @authenticated
    @catch_error
    async def post(self, approval_id):
        """
        Approve a institution approval.

        Args:
            approval_id (str): id of inst approval request
        """
        insts = await self.get_admin_institutions()
        ret = await self.db.inst_approvals.find({'id': approval_id})
        if not ret:
            raise HTTPError(404, 'no record for approval_id')
        if not any(ret['experiment'] == exp and ret['institution'] == insts[exp] for exp in insts):
            raise HTTPError(403, 'invalid authorization')

        audit_logger.info(f'{self.auth_data["username"]} is approving request {approval_id}')
        if ret['newuser']:
            # create new user account
            user_data = await self.db.user_registrations.find_one({'id': ret['newuser']})
            if not user_data:
                raise HTTPError(400, 'invalid new user')
            # make ascii username
            username = unidecode.unidecode(user_data['first'][0]+user_data['last']).replace("'",'')
            args = {
                "username": username,
                "first_name": user_data['first'],
                "last_name": user_data['last'],
                "email": user_data['external_email'],
                "attribs": {
                    "author_name": user_data['author_name'],
                    "homeDirectory": "",
                }
            }
            await krs.users.create_user(**args)
            await self.db.user_registrations.delete_one({'id': ret['newuser']})
            ret['username'] = username

        # add user to institution
        inst_group = f'/institutions/{ret["experiment"]}/{ret["institution"]}'
        await krs.groups.add_user_group(inst_group, ret['username'])
        if ret['authorlist']:
            await krs.groups.add_user_group(inst_group+'/authorlist', ret['username'])

        if ret['remove_institution']:
            inst_group = f'/institutions/{ret["experiment"]}/{ret["remove_institution"]}'
            await krs.groups.remove_user_group(inst_group, ret['username'])
            await krs.groups.remove_user_group(inst_group+'/authorlist', ret['username'])

        await self.db.inst_approvals.delete_one({'id': approval_id})

        # TODO: send email
        
        self.write({})


class InstApprovalsActionDeny(MyHandler):
    @authenticated
    @catch_error
    async def post(self, approval_id):
        """
        Approve a institution approval.
        """
        insts = await self.get_admin_institutions()
        ret = await self.db.inst_approvals.find({'id': approval_id})
        if not ret:
            raise HTTPError(404, 'no record for approval_id')
        if not any(ret['experiment'] == exp and ret['institution'] == insts[exp] for exp in insts):
            raise HTTPError(403, 'invalid authorization')

        audit_logger.info(f'{self.auth_data["username"]} is denying request {approval_id}')
        await self.db.inst_approvals.delete_one({'id': approval_id})

        # TODO: send email

        self.write({})
