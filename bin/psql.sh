#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )


# shellcheck source=config/env
. "/var/snap/gogs/current/config/env"

${DIR}/postgresql/bin/psql.sh -p ${PSQL_PORT} -h ${PSQL_DATABASE} "$@"
