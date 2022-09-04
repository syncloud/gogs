#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi

export USER=git
export HOME=/home/git
export PATH=$DIR/git/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

case $1 in
start)
    ${DIR}/bin/postgresql-post-start.sh
    exec ${DIR}/bin/gogs web --config /var/snap/gogs/current/config/gogs.ini
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac

