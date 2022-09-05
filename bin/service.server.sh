#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi

export USER=git
export HOME=/home/git
export PATH=$DIR/git/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

function wait_for_db() {
    started=0
    echo "waiting for gogs db"
    set +e
    for i in $(seq 1 30); do
      ${DIR}/bin/psql.sh -c "select 1;" gogs
      if [[ $? == 0 ]]; then
        started=1
        break
      fi
      echo "Tried $i times. Waiting 5 secs..."
      sleep 5
    done
    set -e
    if [[ $started == 0 ]]; then
        exit 1
    fi
    echo "done waiting for gogs db"
}


case $1 in
start)
    wait_for_db
    exec ${DIR}/bin/gogs web --config /var/snap/gogs/current/config/gogs.ini
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
