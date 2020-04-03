# keycloak-rest-services
Services surrounding KeyCloak, that use the REST API to read/update state.

[![CircleCI](https://circleci.com/gh/WIPACrepo/keycloak-rest-services.svg?style=svg&circle-token=87c420d0b5ba0dffb28337618e7cf0df7a905bf8)](https://circleci.com/gh/WIPACrepo/keycloak-rest-services)

* [Basic Design](#basic-design)
  + [Direct Actions](#direct-actions)
  + [Approval Actions](#approval-actions)
* [Running Tests](#running-tests)
  + [Getting Test Coverage](#getting-test-coverage)
* [Manually Running Scripts](#manually-running-scripts)

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

## Running Tests

The tests run automatically in CircleCI, but for those that want to run them
locally, there is a way.

First, build and load the local python environment:

    ./setupenv.sh
    . env/bin/activate

Then, start an instance of KeyCloak in another terminal:

    docker run --rm -it -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin --network host jboss/keycloak:8.0.2 -Djboss.bind.address.private=127.0.0.1 -Djboss.bind.address=127.0.0.1

KeyCloak may take a minute to start.  If it does not, check your network settings,
as it does not play well with VPNs and other more exotic network situations.

Finally, run the tests:

    keycloak_url=http://localhost:8080 username=admin password=admin pytest

### Getting Test Coverage

If you want a coverage report, instead of running pytest directly, run it
under the coverage tool:

    keycloak_url=http://localhost:8080 username=admin password=admin coverage run -m pytest
    coverage html --include='krs*'

## Manually Running Scripts

It is possible to manually run all of the basic operations for controlling users
and groups.

1. Bootstrap KeyCloak

    If you do not already have a KeyCloak instance, start a test instance as shown above.
    Then, run the bootstrap script to create a realm and the REST service account:

    ```bash
    keycloak_url=http://localhost:8080 username=admin password=admin realm=test python3 -m krs.bootstrap
    ```

    Save the `client_secret` that gets printed, as you will need this.

2. User and group actions

    Now you can actually run the scripts, which take the format:

    ```bash
    keycloak_url=http://localhost:8080 client_id=rest-access client_secret=<SECRET> realm=test python -m krs.<SCRIPT> <ARGS>
    ```

    As an example, to list all groups:

    ```bash
    keycloak_url=http://localhost:8080 client_id=rest-access client_secret=<SECRET> realm=test python -m krs.groups list
    ```
