# keycloak-rest-services
Services surrounding KeyCloak, that use the REST API to read/update state.

[![CircleCI](https://circleci.com/gh/WIPACrepo/keycloak-rest-services/tree/master.svg?style=shield)](https://circleci.com/gh/WIPACrepo/keycloak-rest-services/tree/master)


## Basic Design

### Direct Actions

Any action that does not require approval will be made directly against
KeyCloak using the REST API.

### Approval Actions

Approval actions require temporary storage to hold the action until approval
has been granted.  Any database would do, but we have chosen MongoDB for
several reasons:

1. We are already familiar with it and use it in several other projects.
2. It can expire entries automatically with TTL Indexes.
3. Tailable cursors allow "watching" changes in real time.

Once approval has been granted, the action will then be applied to KeyCloak.

## Bootstrap KeyCloak

First, get a KeyCloak instance running.  For testing, the Docker container works:

    docker run --rm -it -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin --network host jboss/keycloak:8.0.2 -Djboss.bind.address.private=127.0.0.1 -Djboss.bind.address=127.0.0.1

Then, run the bootstrap script:

    realm=test keycloak_url=http://localhost:8080 username=admin password=admin python3 -m krs.bootstrap
