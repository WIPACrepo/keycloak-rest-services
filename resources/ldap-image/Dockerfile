FROM osixia/openldap:1.5.0

COPY resources/ldap-ldifs /container/service/slapd/assets/config/bootstrap/ldif/custom

# basic env settings
# PORT=1389
ENV LDAP_ORGANIZATION="IceCube"
ENV LDAP_DOMAIN="icecube.wisc.edu"

# can override
ENV LDAP_ADMIN_PASSWORD=admin
