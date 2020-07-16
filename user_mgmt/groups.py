"""
Handle group mamagement actions.
"""
import logging
import uuid

from tornado.web import HTTPError
from rest_tools.server import catch_error, authenticated

import krs.users
import krs.groups

from . import MyHandler


class MultiGroups(MyHandler):
    @authenticated
    @catch_error
    async def get(self):
        """Get a list of all groups."""
        ret = await krs.groups.list_groups(token=self.token)
        groups = set()
        for group in ret:
            val = group.strip('/').split('/')
            # only select groups that can be administered by users
            if len(val) > 1 and val[0] != 'institutions' and val[-1] == '_admin':
                groups.add(group[:-6])
        # get sub-groups of administered groups
        for group in ret:
            if (not group.rsplit('/')[-1].startswith('_')) and any(g.startswith(group) for g in groups):
                groups.add(group)
        self.write(sorted(exps))


class Group(MyHandler):
    @authenticated
    @catch_error
    async def get(self, group):
        """
        Get members of a group.  Must be admin.

        Args:
            group (str): group path
        Returns:
            list: usernames
        """
        if group.rsplit('/')[-1].startswith('_'):
            raise HTTPError(400, 'bad group request')
        admin_groups = await self.get_admin_groups()
        if not any(group.startswith(g) for g in admin_groups):
            raise HTTPError(403, 'invalid authorization')
        try:
            ret = await krs.groups.get_group_membership(token=self.token)
        except Exception:
            raise HTTPError(404, 'group does not exist')
        self.write(sorted(ret))


class GroupUser(MyHandler):
    @authenticated
    @catch_error
    async def put(self, group, username):
        """
        Add a user to a group.  Must be admin.

        Args:
            group (str): group path
            username (str): username of new member
        Returns:
            list: usernames
        """
        if group.rsplit('/')[-1].startswith('_'):
            raise HTTPError(400, 'bad group request')
        admin_groups = await self.get_admin_groups()
        if not any(group.startswith(g) for g in admin_groups):
            raise HTTPError(403, 'invalid authorization')
        await krs.groups.add_user_group(group, username)
        self.write({})

    @authenticated
    @catch_error
    async def delete(self, group, username):
        """
        Remove a user from a group.  Must be admin or the user in question.

        Args:
            group (str): group path
            username (str): username of new member
        Returns:
            list: usernames
        """
        if group.rsplit('/')[-1].startswith('_'):
            raise HTTPError(400, 'bad group request')
        admin_groups = await self.get_admin_groups()
        if username != self.auth_data['username'] and not any(group.startswith(g) for g in admin_groups):
            raise HTTPError(403, 'invalid authorization')
        await krs.groups.remove_user_group(group, username)
        self.write({})


class GroupApprovals(MyHandler):
    @authenticated
    @catch_error
    async def post(self):
        """New group approval request"""
        logging.info('new group request')

        req_fields = {
            'group': str,
        }
        opt_fields = {}
        approval_data = self.json_filter(req_fields, opt_fields)
        approval_data['username'] = self.auth_data['username']
        approval_data['id'] = uuid.uuid1().hex

        if approval_data['group'].rsplit('/')[-1].startswith('_'):
            raise HTTPError(400, 'bad group request')

        await self.db.group_approvals.insert_one(approval_data)

        self.set_status(201)
        self.write({})

    @authenticated
    @catch_error
    async def get(self):
        """Get list of requests a user can approve"""
        admin_groups = await self.get_admin_groups()
        search = {'group': {'$in': list(admin_groups)}}
        ret = await self.db.group_approvals.find(search)
        self.write(ret)


class GroupApprovalsActionApprove(MyHandler):
    @authenticated
    @catch_error
    async def put(self, approval_id):
        """
        Approve a group approval.

        Args:
            approval_id (str): id of group approval request
        """
        admin_groups = await self.get_admin_groups()
        ret = await self.db.group_approvals.find_one({'id': approval_id})
        if not ret:
            raise HTTPError(404, 'no record for approval_id')
        if not any(ret['group'].startswith(g) for g in admin_groups):
            raise HTTPError(403, 'invalid authorization')

        audit_logger.info(f'{self.auth_data["username"]} is approving request {approval_id}')

        # add user to group
        await krs.groups.add_user_group(ret['group'], ret['username'])

        # clean up approval
        await self.db.group_approvals.delete_one({'id': approval_id})

        # TODO: send email
        
        self.write({})


class GroupApprovalsActionDeny(MyHandler):
    @authenticated
    @catch_error
    async def put(self, approval_id):
        """
        Deny a group approval.

        Args:
            approval_id (str): id of group approval request
        """
        admin_groups = await self.get_admin_groups()
        ret = await self.db.group_approvals.find_one({'id': approval_id})
        if not ret:
            raise HTTPError(404, 'no record for approval_id')
        if not any(ret['group'].startswith(g) for g in admin_groups):
            raise HTTPError(403, 'invalid authorization')

        audit_logger.info(f'{self.auth_data["username"]} is denying request {approval_id}')
        await self.db.group_approvals.delete_one({'id': approval_id})

        # TODO: send email

        self.write({})

