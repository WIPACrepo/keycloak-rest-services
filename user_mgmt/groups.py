"""
Handle group mamagement actions.
"""
import logging
import uuid

from tornado.web import HTTPError
from rest_tools.server import catch_error, authenticated

import krs.users
import krs.groups

from .handler import MyHandler

audit_logger = logging.getLogger('audit')


def is_authorized_group(group, auth_groups):
    if group in auth_groups:
        return True
    # sub-groups of auth_groups are authorized as well
    return any(len(group) > len(g) and group[len(g)] == '/' and group.startswith(g) for g in auth_groups)

def get_administered_groups(ret):
    groups = {}
    for group in ret:
        val = group.strip('/').split('/')
        # only select groups that can be administered by users
        if len(val) > 1 and val[0] != 'institutions' and val[-1] == '_admin':
            groups[group[:-7]] = ret[group[:-7]]['id']
    # get sub-groups of administered groups
    for group in ret:
        if (not group.rsplit('/')[-1].startswith('_')) and is_authorized_group(group, groups):
            groups[group] = ret[group]['id']
    return groups


class MultiGroups(MyHandler):
    @authenticated
    @catch_error
    async def get(self):
        """Get a list of all groups."""
        ret = await self.group_cache.list_groups()
        self.write(get_administered_groups(ret))


class Group(MyHandler):
    @authenticated
    @catch_error
    async def get(self, group_id):
        """
        Get members of a group.  Must be admin.

        Args:
            group_id (str): group id
        Returns:
            list: usernames
        """
        try:
            group = await self.group_cache.get_group_info_from_id(group_id)
        except Exception:
            raise HTTPError(404, 'group does not exist')

        if group['name'].startswith('_'):
            raise HTTPError(400, 'bad group request')
        admin_groups = await self.get_admin_groups()
        if not is_authorized_group(group['path'], admin_groups):
            raise HTTPError(403, 'invalid authorization')

        ret = await self.group_cache.get_members(group['path'])
        self.write(sorted(ret))


class GroupUser(MyHandler):
    @authenticated
    @catch_error
    async def put(self, group_id, username):
        """
        Add a user to a group.

        Must be admin.

        Args:
            group_id (str): group id
            username (str): username of new member
        """
        try:
            group = await self.group_cache.get_group_info_from_id(group_id)
        except Exception:
            raise HTTPError(404, 'group does not exist')

        if group['name'].startswith('_'):
            raise HTTPError(400, 'bad group request')
        admin_groups = await self.get_admin_groups()
        if not is_authorized_group(group['path'], admin_groups):
            raise HTTPError(403, 'invalid authorization')

        try:
            await krs.users.user_info(username, rest_client=self.krs_client)
        except Exception:
            raise HTTPError(404, 'username does not exist')

        await krs.groups.add_user_group(group['path'], username, rest_client=self.krs_client)
        self.group_cache.invalidate(group['path'])
        self.write({})

    @authenticated
    @catch_error
    async def delete(self, group_id, username):
        """
        Remove a user from a group.

        Must be admin or the user in question.

        Args:
            group_id (str): group id
            username (str): username of new member
        """
        try:
            group = await self.group_cache.get_group_info_from_id(group_id)
        except Exception:
            raise HTTPError(404, 'group does not exist')

        if group['name'].startswith('_'):
            raise HTTPError(400, 'bad group request')
        admin_groups = await self.get_admin_groups()
        if not is_authorized_group(group['path'], admin_groups):
            raise HTTPError(403, 'invalid authorization')

        try:
            await krs.users.user_info(username, rest_client=self.krs_client)
        except Exception:
            raise HTTPError(404, 'username does not exist')

        await krs.groups.remove_user_group(group['path'], username, rest_client=self.krs_client)
        self.group_cache.invalidate(group['path'])
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

        ret = await self.group_cache.list_groups()
        groups = get_administered_groups(ret)
        if approval_data['group'] not in groups:
            logging.info(f'{approval_data}\n{groups}')
            raise HTTPError(400, 'bad group request')
        approval_data['group_id'] = groups[approval_data['group']]

        await self.db.group_approvals.insert_one(approval_data)

        # send email to admins
        await self.send_admin_email(approval_data['group'], f'''IceCube Group Request

A request for membership to {approval_data["group"]}
has been made by user {approval_data["username"]}.

Please approve or deny this request by going to:
  https://user-management.icecube.aq/groups

Documentation is located at:
  https://docs.icecube.aq/Madison-account/user-workflow/admin_groups/
''')

        self.set_status(201)
        self.write({'id': approval_data['id']})

    @authenticated
    @catch_error
    async def get(self):
        """Get list of requests a user can approve"""
        admin_groups = await self.get_admin_groups()
        ret = []
        if admin_groups:
            search = {'group': {'$in': list(admin_groups)}}
            async for row in self.db.group_approvals.find(search, projection={'_id': False}):
                ret.append(row)
        self.write(ret)


class GroupApprovalsActionApprove(MyHandler):
    @authenticated
    @catch_error
    async def post(self, approval_id):
        """
        Approve a group approval.

        Args:
            approval_id (str): id of group approval request
        """
        admin_groups = await self.get_admin_groups()
        ret = await self.db.group_approvals.find_one({'id': approval_id})
        if not ret:
            raise HTTPError(404, 'no record for approval_id')
        if not is_authorized_group(ret['group'], admin_groups):
            raise HTTPError(403, 'invalid authorization')

        audit_logger.info(f'{self.auth_data["username"]} is approving request {approval_id}')

        # add user to group
        await krs.groups.add_user_group(ret['group'], ret['username'], rest_client=self.krs_client)
        self.group_cache.invalidate(ret['group'])

        # clean up approval
        await self.db.group_approvals.delete_one({'id': approval_id})

        # send email
        try:
            try:
                args = await krs.users.user_info(ret['username'], rest_client=self.krs_client)
            except Exception:
                raise HTTPError(400, 'invalid username')
            krs.email.send_email(
                recipient={'name': f'{args["firstName"]} {args["lastName"]}', 'email': args['email']},
                subject='IceCube Group Request Approved',
                content=f'''IceCube Group Request Approved

Your group request for {ret["group"]} has been approved.
''')
        except Exception:
            logging.warning('failed to send email for group approval', exc_info=True)

        self.write({})


class GroupApprovalsActionDeny(MyHandler):
    @authenticated
    @catch_error
    async def post(self, approval_id):
        """
        Deny a group approval.

        Args:
            approval_id (str): id of group approval request
        """
        admin_groups = await self.get_admin_groups()
        ret = await self.db.group_approvals.find_one({'id': approval_id})
        if not ret:
            raise HTTPError(404, 'no record for approval_id')
        if not is_authorized_group(ret['group'], admin_groups):
            raise HTTPError(403, 'invalid authorization')

        audit_logger.info(f'{self.auth_data["username"]} is denying request {approval_id}')
        await self.db.group_approvals.delete_one({'id': approval_id})

        # send email
        try:
            try:
                args = await krs.users.user_info(ret['username'], rest_client=self.krs_client)
            except Exception:
                raise HTTPError(400, 'invalid username')
            krs.email.send_email(
                recipient={'name': f'{args["firstName"]} {args["lastName"]}', 'email': args['email']},
                subject='IceCube Group Request Denied',
                content=f'''IceCube Group Request Denied

Your group request for {ret["group"]} has been denied.
''')
        except Exception:
            logging.warning('failed to send email for group deny', exc_info=True)

        self.write({})
