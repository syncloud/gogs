#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
${DIR}/../build/snap/bin/gogs --version

mkdir -p /snap/gogs
ln -s $(realpath ${DIR}/../build/snap) /snap/gogs/current
/snap/gogs/current/app/gogs/gogs --version
