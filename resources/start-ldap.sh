#!/bin/bash
podman run -d --name ldap -p 1389:1389 -v $PWD/resources/ldap-ldifs:/ldifs --env LDAP_PORT_NUMBER=1389 --env LDAP_ADMIN_USERNAME=admin \
 --env LDAP_ADMIN_PASSWORD=admin --env 'LDAP_ROOT=dc=icecube,dc=wisc,dc=edu' \
 --env 'LDAP_CUSTOM_LDIF_DIR=/ldifs' \
 --env 'BITNAMI_DEBUG=true' \
 bitnami/openldap:2.6.10
sleep 2

echo "server at: localhost:1389"
echo "admin login: cn=admin,dc=icecube,dc=wisc,dc=edu"
echo "LDAP Ready"

( trap exit SIGINT ; read -r -d '' _ </dev/tty ) ## wait for Ctrl-C

echo "Stopping LDAP"
podman stop ldap
podman rm ldap
