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
    addr_parts = saved_addr.split('/')
    try:
        rest_client.address = '/'.join(addr_parts[:3]) + '/auth/admin'
        server_info = await rest_client.request('GET', '/serverinfo')
    finally:
        rest_client.address = saved_addr
    ver = server_info['version']
    return ver
