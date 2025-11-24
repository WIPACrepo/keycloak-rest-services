FROM symas/openldap:2

COPY resources/ldap-ldifs /ldifs

# basic env settings
ENV LDAP_PORT_NUMBER=1389
ENV LDAP_CUSTOM_LDIF_DIR=/ldifs
ENV LDAP_ROOT="dc=icecube,dc=wisc,dc=edu"

# can override
ENV LDAP_ADMIN_USERNAME=admin
ENV LDAP_ADMIN_PASSWORD=admin
