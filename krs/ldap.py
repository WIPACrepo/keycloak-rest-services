import logging

from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, MODIFY_ADD, MODIFY_REPLACE, MODIFY_DELETE
from rest_tools.client import RestClient
from wipac_dev_tools import from_environment

logger = logging.getLogger('krs.ldap')


class LDAP:
    """
    LDAP client with a few basic actions to suppliment Keycloak
    """
    def __init__(self):
        self.config = from_environment({
            'LDAP_URL': None,
            'LDAP_ADMIN_USER': 'cn=admin,dc=icecube,dc=wisc,dc=edu',
            'LDAP_ADMIN_PASSWORD': 'admin',
            'LDAP_USER_BASE': 'ou=People,dc=icecube,dc=wisc,dc=edu',
            'LDAP_GROUP_BASE': 'ou=Group,dc=icecube,dc=wisc,dc=edu',
        })

    async def keycloak_ldap_link(self, keycloak_token=None):
        cfg = from_environment({
            'KEYCLOAK_URL': None,
            'KEYCLOAK_REALM': None,
        })
        base_url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{cfg["KEYCLOAK_REALM"]}'
        rc = RestClient(base_url, keycloak_token)
        url = '/components'

        ret = await rc.request('GET', url)
        ldapComponentId = None
        ldapAttrs = []
        for comp in ret:
            if 'providerId' in comp:
                if comp['providerId'] == 'ldap':
                    ldapComponentId = comp['id']
                elif comp['providerId'] == 'user-attribute-ldap-mapper':
                    ldapAttrs.append(comp['name'])
        if ldapComponentId:
            logger.warning('LDAP is already linked to Keycloak')
            return

        # define LDAP provider
        args = {
            'name': 'ldap',
            'providerId': 'ldap',
            'providerType': 'org.keycloak.storage.UserStorageProvider',
            'config': {
                'connectionUrl': [self.config['LDAP_URL']],
                'bindCredential': [self.config['LDAP_ADMIN_PASSWORD']],
                'bindDn': [self.config['LDAP_ADMIN_USER']],
                'usersDn': [self.config['LDAP_USER_BASE']],
                'userObjectClasses': ['inetOrgPerson, organizationalPerson'],
                'usernameLDAPAttribute': ['uid'],
                'uuidLDAPAttribute': ['uid'],
                'rdnLDAPAttribute': ['uid'],
                'fullSyncPeriod': ['604800'],
                'pagination': ['true'],
                'connectionPooling': ['true'],
                'cachePolicy': ['DEFAULT'],
                'useKerberosForPasswordAuthentication': ['false'],
                'importEnabled': ['true'],
                'enabled': ['true'],
                'changedSyncPeriod': ['60'],
                'lastSync': ['-1'],
                'vendor': ['other'],
                'allowKerberosAuthentication': ['false'],
                'syncRegistrations': ['true'],
                'authType': ['simple'],
                'debug': ['false'],
                'searchScope': ['1'],
                'useTruststoreSpi': ['ldapsOnly'],
                'trustEmail': ['false'],
                'priority': ['0'],
                'editMode': ['WRITABLE'],
                'validatePasswordPolicy': ['false'],
                'batchSizeForSync': ['1000'],
            }
        }
        await rc.request('POST', url, args)
        ret = await rc.request('GET', url)
        ldapComponentId = None
        ldapAttrs = []
        for comp in ret:
            if 'providerId' in comp:
                if comp['providerId'] == 'ldap':
                    ldapComponentId = comp['id']
                elif comp['providerId'].endswith('ldap-mapper'):
                    ldapAttrs.append(comp['name'])
        if not ldapComponentId:
            raise RuntimeError('LDAP provider not registered in Keycloak')

        # define mandatory attrs
        if 'username' not in ldapAttrs:
            args = {
                'name': 'username',
                'providerId': 'user-attribute-ldap-mapper',
                'providerType': 'org.keycloak.storage.ldap.mappers.LDAPStorageMapper',
                'parentId': ldapComponentId,
                'config': {
                    'is.mandatory.in.ldap': ['true'],
                    'always.read.value.from.ldap': ['false'],
                    'read.only': ['false'],
                    'user.model.attribute': ['username'],
                    'ldap.attribute': ['uid'],
                }
            }
            await rc.request('POST', url, args)

        if 'first name' not in ldapAttrs:
            args = {
                'name': 'first name',
                'providerId': 'user-attribute-ldap-mapper',
                'providerType': 'org.keycloak.storage.ldap.mappers.LDAPStorageMapper',
                'parentId': ldapComponentId,
                'config': {
                    'is.mandatory.in.ldap': ['true'],
                    'always.read.value.from.ldap': ['true'],
                    'read.only': ['false'],
                    'user.model.attribute': ['firstName'],
                    'ldap.attribute': ['givenName'],
                }
            }
            await rc.request('POST', url, args)

        if 'last name' not in ldapAttrs:
            args = {
                'name': 'last name',
                'providerId': 'user-attribute-ldap-mapper',
                'providerType': 'org.keycloak.storage.ldap.mappers.LDAPStorageMapper',
                'parentId': ldapComponentId,
                'config': {
                    'is.mandatory.in.ldap': ['true'],
                    'always.read.value.from.ldap': ['true'],
                    'read.only': ['false'],
                    'user.model.attribute': ['lastName'],
                    'ldap.attribute': ['sn'],
                }
            }
            await rc.request('POST', url, args)

        if 'fullname' not in ldapAttrs:
            args = {
                'name': 'fullname',
                'providerId': 'full-name-ldap-mapper',
                'providerType': 'org.keycloak.storage.ldap.mappers.LDAPStorageMapper',
                'parentId': ldapComponentId,
                'config': {
                    'read.only': ['false'],
                    'write.only': ['true'],
                    'ldap.full.name.attribute': ['cn'],
                }
            }
            await rc.request('POST', url, args)

        if 'email' not in ldapAttrs:
            args = {
                'name': 'email',
                'providerId': 'user-attribute-ldap-mapper',
                'providerType': 'org.keycloak.storage.ldap.mappers.LDAPStorageMapper',
                'parentId': ldapComponentId,
                'config': {
                    'is.mandatory.in.ldap': ['true'],
                    'always.read.value.from.ldap': ['false'],
                    'read.only': ['false'],
                    'user.model.attribute': ['email'],
                    'ldap.attribute': ['mail'],
                }
            }
            await rc.request('POST', url, args)

        # define optional attrs
        for attr in ('uidNumber', 'gidNumber', 'homeDirectory', 'loginShell'):
            if attr not in ldapAttrs:
                args = {
                    'name': attr,
                    'providerId': 'user-attribute-ldap-mapper',
                    'providerType': 'org.keycloak.storage.ldap.mappers.LDAPStorageMapper',
                    'parentId': ldapComponentId,
                    'config': {
                        'is.mandatory.in.ldap': ['false'],
                        'always.read.value.from.ldap': ['false'],
                        'read.only': ['false'],
                        'user.model.attribute': [attr],
                        'ldap.attribute': [attr],
                    }
                }
                await rc.request('POST', url, args)

    async def force_keycloak_sync(self, keycloak_client=None):
        logger.info('syncing keycloak and ldap')
        ret = await keycloak_client.request('GET', '/components')
        ldapComponentId = None
        for comp in ret:
            if 'providerId' in comp and comp['providerId'] == 'ldap':
                ldapComponentId = comp['id']
                break
        if not ldapComponentId:
            raise RuntimeError('LDAP provider not registered in Keycloak')

        try:
            await keycloak_client.request('POST', f'/user-storage/{ldapComponentId}/sync?action=triggerChangedUsersSync')
        except Exception as e:
            logger.info(f'error: {e.response.text}')
            raise

    def list_users(self, attrs=None):
        """
        List user information in LDAP.

        Args:
            attrs (list): attributes from each user to return (default: ALL)

        Returns:
            dict: username: attr dict
        """
        # define the server
        s = Server(self.config['LDAP_URL'], get_info=ALL)

        # define the connection
        c = Connection(s, auto_bind=True)

        # search for the user
        c.search(self.config['LDAP_USER_BASE'], '(uid=*)', attributes=ALL_ATTRIBUTES, paged_size=100)
        if c.result['result']:
            logger.debug(f'search result {c.result}')
            raise Exception(f'Search users failed: {c.result["description"]}')
        cookie = c.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']

        def process():
            for entry in c.entries:
                entry = entry.entry_attributes_as_dict
                if attrs:
                    val = {k: (entry[k][0] if len(entry[k]) == 1 else entry[k]) for k in entry if k in attrs}
                else:
                    val = {k: (entry[k][0] if len(entry[k]) == 1 else entry[k]) for k in entry}
                ret[entry['uid'][0]] = val

        ret = {}
        process()
        while cookie:
            c.search(self.config['LDAP_USER_BASE'], '(uid=*)', attributes=ALL_ATTRIBUTES, paged_size=100, paged_cookie=cookie)
            if c.result['result']:
                logger.debug(f'search result {c.result}')
                raise Exception(f'Search users failed: {c.result["description"]}')
            cookie = c.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']
            process()

        return ret

    def get_user(self, username):
        """
        Get user information from LDAP.

        Args:
            username (str): username of user

        Returns:
            dict: user info

        Raises:
            KeyError
        """
        # define the server
        s = Server(self.config['LDAP_URL'], get_info=ALL)

        # define the connection
        c = Connection(s, auto_bind=True)

        # search for the user
        ret = c.search(self.config['LDAP_USER_BASE'], f'(uid={username})', attributes=ALL_ATTRIBUTES)
        if not ret:
            raise KeyError(f'user {username} not found')
        return c.entries[0]

    def create_user(self, username, firstName, lastName, email):
        """
        Add a user to LDAP.

        Args:
            username (str): username of user
            firstName (str): first name of user
            lastName (str): last name of user
            email (str): email of user
        """
        # define the server
        s = Server(self.config['LDAP_URL'], get_info=ALL)

        # define the connection
        c = Connection(s, user=self.config['LDAP_ADMIN_USER'], password=self.config['LDAP_ADMIN_PASSWORD'], auto_bind=True)

        # check if user already exists
        ret = c.search(self.config['LDAP_USER_BASE'], f'(uid={username})')
        if ret:
            raise Exception(f'User {username} already exists')

        # perform the Add operation
        objectClasses = ['inetOrgPerson', 'organizationalPerson', 'person', 'top']
        attrs = {
            'cn': f'{firstName} {lastName}',
            'sn': lastName,
            'givenName': firstName,
            'mail': email,
            'uid': username,
        }
        ret = c.add(f'uid={username},{self.config["LDAP_USER_BASE"]}', objectClasses, attrs)
        if not ret:
            raise Exception(f'Create user {username} failed: {c.result["message"]}')

        # close the connection
        c.unbind()

    def modify_user(self, username, attributes=None, objectClass=None, removeObjectClass=None):
        """
        Modify a user in LDAP.

        Args:
            username (str): username in LDAP
            attributes (dict): attributes to modify
            objectClass (str): objectClass to add (default: None)
            removeObjectClass (str): objectClass to remove (default: None)
        """
        if not attributes:
            attributes = {}

        # define the server
        s = Server(self.config['LDAP_URL'], get_info=ALL)

        # define the connection
        c = Connection(s, user=self.config['LDAP_ADMIN_USER'], password=self.config['LDAP_ADMIN_PASSWORD'], auto_bind=True, raise_exceptions=True)

        # check if user exists
        ret = c.search(self.config['LDAP_USER_BASE'], f'(uid={username})', attributes=ALL_ATTRIBUTES)
        if not ret:
            raise Exception(f'User {username} does not exist')
        ret = c.entries[0]

        vals = {}
        for a in attributes:
            v = attributes[a] if isinstance(attributes[a], list) else [attributes[a]]
            if attributes[a] is None:
                if a in ret:
                    vals[a] = [(MODIFY_DELETE, [])]
                else:
                    continue  # trying to delete an attr that doesn't exist
            elif a in ret:
                vals[a] = [(MODIFY_REPLACE, v)]
            else:
                vals[a] = [(MODIFY_ADD, v)]

        if objectClass and removeObjectClass:
            raise Exception('cannot add and remove object classes at once')
        elif objectClass and objectClass not in ret['objectClass']:
            vals['objectClass'] = [(MODIFY_ADD, [objectClass])]
        elif removeObjectClass and removeObjectClass in ret['objectClass']:
            vals['objectClass'] = [(MODIFY_DELETE, [removeObjectClass])]

        # perform the operation
        logger.debug(f'ldap change for user {username}: {vals}')
        try:
            ret = c.modify(f'uid={username},{self.config["LDAP_USER_BASE"]}', vals)
        except Exception:
            logger.debug('ldap exception', exc_info=True)
            raise Exception(f'Modify user {username} failed')

        # close the connection
        c.unbind()

    def list_groups(self, groupbase=None, attrs=None):
        """
        List group information in LDAP.

        Args:
            groupbase (str): (optional) base (OU) of group
            attrs (list): attributes from each group to return (default: ALL)

        Returns:
            dict: groupname: attr dict
        """
        if not groupbase:
            groupbase = self.config['LDAP_GROUP_BASE']

        # define the server
        s = Server(self.config['LDAP_URL'], get_info=ALL)

        # define the connection
        c = Connection(s, auto_bind=True)

        # paged search for the group
        c.search(groupbase, '(cn=*)', attributes=ALL_ATTRIBUTES, paged_size=100)
        if c.result['result']:
            logger.debug(f'search result {c.result}')
            raise Exception(f'Search groups failed: {c.result["description"]}')
        cookie = c.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']

        def process():
            for entry in c.entries:
                entry = entry.entry_attributes_as_dict
                if attrs:
                    val = {k: (entry[k][0] if len(entry[k]) == 1 else entry[k]) for k in entry if k in attrs}
                else:
                    val = {k: (entry[k][0] if len(entry[k]) == 1 else entry[k]) for k in entry}
                ret[entry['cn'][0]] = val

        ret = {}
        process()
        while cookie:
            c.search(groupbase, '(cn=*)', attributes=ALL_ATTRIBUTES, paged_size=100, paged_cookie=cookie)
            if c.result['result']:
                logger.debug(f'search result {c.result}')
                raise Exception(f'Search groups failed: {c.result["description"]}')
            cookie = c.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']
            process()

        return ret

    def get_group(self, groupname, groupbase=None):
        """
        Get group information from LDAP.

        Args:
            groupname (str): name of group
            groupbase (str): (optional) base (OU) of group

        Returns:
            dict: group info

        Raises:
            KeyError
        """
        if not groupbase:
            groupbase = self.config['LDAP_GROUP_BASE']

        # define the server
        s = Server(self.config['LDAP_URL'], get_info=ALL)

        # define the connection
        c = Connection(s, auto_bind=True)

        # search for the group
        ret = c.search(groupbase, f'(cn={groupname})', attributes=ALL_ATTRIBUTES)
        if not ret:
            raise KeyError(f'Group {groupname} not found')
        entry = c.entries[0].entry_attributes_as_dict
        return {k: (entry[k][0] if len(entry[k]) == 1 else entry[k]) for k in entry}

    def create_group(self, groupname, groupbase=None, gidNumber=None):
        """
        Add a group to LDAP.

        Args:
            groupname (str): name of group
            groupbase (str): (optional) base (OU) of group
            gidNumber (int): for posix groups, gid number of group
        """
        if not groupbase:
            groupbase = self.config['LDAP_GROUP_BASE']

        # define the server
        s = Server(self.config['LDAP_URL'], get_info=ALL)

        # define the connection
        c = Connection(s, user=self.config['LDAP_ADMIN_USER'], password=self.config['LDAP_ADMIN_PASSWORD'], auto_bind=True)

        # check if group already exists
        ret = c.search(groupbase, f'(cn={groupname})')
        if ret:
            raise Exception(f'Group {groupname} already exists')

        # perform the Add operation
        objectClasses = ['posixGroup' if gidNumber else 'groupOfNames', 'top']
        attrs = {
            'cn': groupname,
        }
        if gidNumber:
            attrs['gidNumber'] = gidNumber
        else:
            attrs['member'] = 'cn=empty-membership-placeholder'
        ret = c.add(f'cn={groupname},{groupbase}', objectClasses, attrs)
        if not ret:
            raise Exception(f'Create group {groupname} failed: {c.result["message"]}')

        # close the connection
        c.unbind()

    def add_user_group(self, username, groupname, groupbase=None):
        """
        Add a user to a group in LDAP.

        Args:
            username (str): name of user
            groupname (str): name of group
            groupbase (str): (optional) base (OU) of group
        """
        if not groupbase:
            groupbase = self.config['LDAP_GROUP_BASE']

        # define the server
        s = Server(self.config['LDAP_URL'], get_info=ALL)

        # define the connection
        c = Connection(s, user=self.config['LDAP_ADMIN_USER'], password=self.config['LDAP_ADMIN_PASSWORD'], auto_bind=True)

        # check if group exists
        ret = c.search(groupbase, f'(cn={groupname})', attributes=ALL_ATTRIBUTES)
        if not ret:
            raise Exception(f'Group {groupname} does not exist')
        ret = c.entries[0].entry_attributes_as_dict

        vals = {}
        if 'gidNumber' in ret:  # posix group
            if 'memberUid' in ret and username in ret['memberUid']:
                return
            else:
                vals['memberUid'] = [(MODIFY_ADD), [username]]
        else:
            user_cn = f'uid={username},{self.config["LDAP_USER_BASE"]}'
            if 'member' in ret and user_cn in ret['member']:
                return
            else:
                vals['member'] = [(MODIFY_ADD), [user_cn]]

        # perform the operation
        logger.debug(f'ldap change for group {groupname}: {vals}')
        try:
            ret = c.modify(f'cn={groupname},{groupbase}', vals)
            if c.result['result']:
                logger.debug(f'modify ldap error: {c.result["message"]}')
                raise Exception(f'Add user {username} to group {username} failed')
        except Exception:
            logger.debug('ldap exception', exc_info=True)
            raise Exception(f'Add user {username} to group {username} failed')

        # close the connection
        c.unbind()

    def remove_user_group(self, username, groupname, groupbase=None):
        """
        Remove a user from a group in LDAP.

        Args:
            username (str): name of user
            groupname (str): name of group
            groupbase (str): (optional) base (OU) of group
        """
        if not groupbase:
            groupbase = self.config['LDAP_GROUP_BASE']

        # define the server
        s = Server(self.config['LDAP_URL'], get_info=ALL)

        # define the connection
        c = Connection(s, user=self.config['LDAP_ADMIN_USER'], password=self.config['LDAP_ADMIN_PASSWORD'], auto_bind=True)

        # check if group exists
        ret = c.search(groupbase, f'(cn={groupname})', attributes=ALL_ATTRIBUTES)
        if not ret:
            raise Exception(f'Group {groupname} does not exist')
        ret = c.entries[0].entry_attributes_as_dict

        vals = {}
        if 'gidNumber' in ret:  # posix group
            if 'memberUid' in ret and username in ret['memberUid']:
                vals['memberUid'] = [(MODIFY_DELETE), [username]]
            else:
                return
        else:
            user_cn = f'uid={username},{self.config["LDAP_USER_BASE"]}'
            if 'member' in ret and user_cn in ret['member']:
                vals['member'] = [(MODIFY_DELETE), user_cn]
            else:
                logger.info('user not in group')
                return

        # perform the operation
        logger.debug(f'ldap change for group {groupname}: {vals}')
        try:
            ret = c.modify(f'cn={groupname},{groupbase}', vals)
        except Exception:
            logger.debug('ldap exception', exc_info=True)
            raise Exception(f'Remove user {username} from group {username} failed')

        # close the connection
        c.unbind()


def get_ldap_members(group):
    """
    Get group members from raw LDAP group information

    Args:
        group (dict): LDAP group info

    Returns:
        list: uids
    """
    if 'member' in group:
        members = group['member']
        if not isinstance(members, list):
            members = [members]
        users = [m.split(',', 1)[0].split('=', 1)[-1] for m in members if m != 'cn=empty-membership-placeholder']
    elif 'memberUid' not in group:
        users = []
    elif isinstance(group['memberUid'], list):
        users = group['memberUid']
    else:
        users = [group['memberUid']]
    return users
