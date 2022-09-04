#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )


# shellcheck source=config/env
. "/var/snap/gogs/current/config/env"

if [[ "$(whoami)" == "git" ]]; then
    ${DIR}/postgresql/bin/psql.sh -p 5433 -h /var/snap/gogs/common/database "$@"
else
    sudo -E -H -u git ${DIR}/postgresql/bin/psql.sh -p 5433 -h /var/snap/gogs/common/database "$@"
fi

