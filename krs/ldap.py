from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, MODIFY_ADD, MODIFY_REPLACE

from rest_tools.server import from_environment


class LDAP:
    """
    LDAP client with a few basic actions to suppliment Keycloak
    """
    def __init__(self):
        self.config = from_environment({
            'LDAP_URL': None,
            'LDAP_ADMIN_USER': 'cn=admin,dc=icecube,dc=wisc,dc=edu',
            'LDAP_ADMIN_PASSWORD': 'admin',
            'LDAP_USER_BASE': 'ou=people,dc=icecube,dc=wisc,dc=edu',
        })

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

    def create_user(self, user):
        """
        Add a user to LDAP.

        Args:
            user (dict): user info to add
        """
        # define the server
        s = Server(self.config['LDAP_URL'], get_info=ALL)

        # define the connection
        c = Connection(s, user=self.config['LDAP_ADMIN_USER'], password=self.config['LDAP_ADMIN_PASSWORD'], auto_bind=True)

        # check if user already exists
        ret = c.search(self.config['LDAP_USER_BASE'], f'(uid={user["username"]})')
        if ret:
            raise Exception(f'User {user["username"]} already exists')

        # perform the Add operation
        ret = c.add(f'uid={user["username"]},{self.config["LDAP_USER_BASE"]}', ['inetOrgPerson', 'organizationalPerson', 'person', 'top'],
            {
                'cn': f'{user["firstName"]} {user["lastName"]}',
                'sn': user['lastName'],
                'givenName': user['firstName'],
                'mail': user['email'],
                'uid': user['username'],
            }
        )
        if not ret:
            raise Exception(f'Create user {user["username"]} failed: {c.result["message"]}')

        # close the connection
        c.unbind()

    def modify_user(self, username, objectClass=None, attributes=None):
        """
        Modify a user in LDAP.

        Args:
            username (str): username in LDAP
            objectClass (str): objectClass to add (default: None)
            attributes (dict): attributes to modify
        """
        # define the server
        s = Server(self.config['LDAP_URL'], get_info=ALL)

        # define the connection
        c = Connection(s, user=self.config['LDAP_ADMIN_USER'], password=self.config['LDAP_ADMIN_PASSWORD'], auto_bind=True)

        # check if user exists
        ret = c.search(self.config['LDAP_USER_BASE'], f'(uid={username})', attributes=ALL_ATTRIBUTES)
        if not ret:
            raise Exception(f'User {username} does not exist')
        ret = c.entries[0]

        vals = {a: [MODIFY_REPLACE if a in ret else MODIFY_ADD, attributes[a] if isinstance(attributes[a], list) else [attributes[a]]] for a in attributes}
        vals['objectClass'] = [MODIFY_ADD, [objectClass]]

        # perform the operation
        ret = c.modify(f'uid={username},{self.config["LDAP_USER_BASE"]}', vals)
        if not ret:
            raise Exception(f'Modify user {user["username"]} failed: {c.result["message"]}')

        # close the connection
        c.unbind()
