troviclient
===========

``troviclient`` is a Python library that can help you interact with the
`Trovi API <https://github.com/chameleoncloud/trovi>`_ for sharing and
storing experimental artifacts.

* `Contributing guide <./DEVELOPMENT.rst>`_

# Setup

Set the following environment variables to your desired values
```
#!/bin/bash
export TROVI_KEYCLOAK_URL="https://auth.chameleoncloud.org/auth"
export TROVI_KEYCLOAK_REALM="chameleon"
export TROVI_OIDC_CLIENT_ID=""
export TROVI_OIDC_CLIENT_SECRET=""
export TROVI_ADMIN=True
export TROVI_BASE_URL="https://trovi.chameleoncloud.org"
```
