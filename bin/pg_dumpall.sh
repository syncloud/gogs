#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

# shellcheck source=config/env
. "/var/snap/gogs/current/config/env"

if [[ "$(whoami)" == "git" ]]; then
    ${DIR}/postgresql/bin/pg_dumpall.sh -p ${PSQL_PORT} -h ${PSQL_DATABASE} "$@"
else
    sudo -E -H -u git ${DIR}/postgresql/bin/pg_dumpall.sh -p ${PSQL_PORT} -h ${PSQL_DATABASE} "$@"
fi
