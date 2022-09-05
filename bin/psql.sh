#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )


# shellcheck source=config/env
. "/var/snap/gogs/current/config/env"

${DIR}/postgresql/bin/psql.sh -p 5433 -U git -h /var/snap/gogs/common/database "$@"
