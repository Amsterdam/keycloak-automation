#!/usr/bin/env bash

# Assert this file is SOURCED, not EXECUTED.
if [ "$0" = "${BASH_SOURCE[0]}" ]; then
    echo "Error: bash script $0 needs to be sourced, not executed." >&2
    exit 1
fi

export KEYCLOAK_BASE_URL='<KEYCLOAK BASE URL'
export KEYCLOAK_REALM='<REALM NAME>'
export KEYCLOAK_USERNAME='<ADMIN USER>'
export KEYCLOAK_PASSWORD='<ADMIN USER PASSWORD>'

