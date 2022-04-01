<!--- Top of README Badges (automated) --->
[![CircleCI](https://img.shields.io/circleci/build/github/WIPACrepo/keycloak-rest-services)](https://app.circleci.com/pipelines/github/WIPACrepo/keycloak-rest-services?branch=master&filter=all) [![PyPI](https://img.shields.io/pypi/v/wipac-keycloak-rest-services)](https://pypi.org/project/wipac-keycloak-rest-services/) [![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/WIPACrepo/keycloak-rest-services?include_prereleases)](https://github.com/WIPACrepo/keycloak-rest-services/) [![PyPI - License](https://img.shields.io/pypi/l/wipac-keycloak-rest-services)](https://github.com/WIPACrepo/keycloak-rest-services/blob/master/LICENSE) [![Lines of code](https://img.shields.io/tokei/lines/github/WIPACrepo/keycloak-rest-services)](https://github.com/WIPACrepo/keycloak-rest-services/) [![GitHub issues](https://img.shields.io/github/issues/WIPACrepo/keycloak-rest-services)](https://github.com/WIPACrepo/keycloak-rest-services/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) [![GitHub pull requests](https://img.shields.io/github/issues-pr/WIPACrepo/keycloak-rest-services)](https://github.com/WIPACrepo/keycloak-rest-services/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen) 
<!--- End of README Badges (automated) --->
# keycloak-rest-services
Services surrounding Keycloak, that use the REST API to read/update state.

[![CircleCI](https://circleci.com/gh/WIPACrepo/keycloak-rest-services.svg?style=svg&circle-token=87c420d0b5ba0dffb28337618e7cf0df7a905bf8)](https://circleci.com/gh/WIPACrepo/keycloak-rest-services)

## Running Tests

The tests run automatically in CircleCI, but for those that want to run them
locally, there is a way.

First, build and load the local python environment:

    ./setupenv.sh
    . env/bin/activate

Then, start an instance of Keycloak in another terminal:

    docker run --rm -it -p 8080:8080 -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin quay.io/keycloak/keycloak:latest -Djboss.bind.address.private=127.0.0.1 -Djboss.bind.address=0.0.0.0

Keycloak may take a minute to start. If it does not, check your network settings,
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

1. Bootstrap Keycloak

    If you do not already have a Keycloak instance, start a test instance as shown above.
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
