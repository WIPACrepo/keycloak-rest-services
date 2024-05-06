async def keycloak_version(rest_client):
    """
    Return the version of the keycloak server rest_client is pointing to.

    In theory, RealmRepresentation that is returned by various Keycloak REST
    API endpoints should contain the keycloakVersion attribute. As of Keycloak
    24.0.1, keycloakVersion is not included, so we have to employ a hack.

    Args:
        rest_client: REST client to a Keycloak server

    Returns:
        str: version string
    """
    saved_addr = rest_client.address
    # make the new address look like https://fqdn/auth/admin
    new_address = '/'.join(saved_addr.split('/')[:3]) + '/auth/admin'
    try:
        rest_client.address = new_address
        server_info = await rest_client.request('GET', '/serverinfo')
    finally:
        rest_client.address = saved_addr
    return server_info['systemInfo']['version']


def fix_singleton_attributes(user_or_group):
    """
    Replace in place the values of user_or_group["attributes"] dictionary
    that are lists with a single element with that element.

    In Keycloak, all custom attribute values of user and group representations
    are lists, even if they have only a single value. This function addresses
    that inconvenience.

    Args:
        user_or_group (dict): user or group object
    """
    if 'attributes' in user_or_group:
        for k in user_or_group['attributes']:
            if len(user_or_group['attributes'][k]) == 1:
                user_or_group['attributes'][k] = user_or_group['attributes'][k][0]
