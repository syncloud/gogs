#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

if [ "$#" -lt 3 ]; then
    echo "usage $0 redirect_domain version device_host"
    exit 1
fi

ARCH=$(uname -m)
DOMAIN=$1
VERSION=$2
DEVICE_HOST=$3

APP=gogs

if [ $ARCH == "x86_64" ]; then
    TEST_SUITE="verify.py test-ui.py"
    SNAP_ARCH=amd64
else
    TEST_SUITE=verify.py
    SNAP_ARCH=armhf
fi

ARCHIVE=${APP}_${VERSION}_${SNAP_ARCH}.snap
APP_ARCHIVE_PATH=$(realpath "$ARCHIVE")

cd ${DIR}

echo ${APP_ARCHIVE_PATH}

cd ${DIR}

attempts=100
attempt=0

set +e
sshpass -p syncloud ssh -o StrictHostKeyChecking=no root@${DEVICE_HOST} date
while test $? -gt 0
do
  if [ $attempt -gt $attempts ]; then
    exit 1
  fi
  sleep 3
  echo "Waiting for SSH $attempt"
  attempt=$((attempt+1))
  sshpass -p syncloud ssh -o StrictHostKeyChecking=no root@${DEVICE_HOST} date
done
set -e

pip2 install -r ${DIR}/dev_requirements.txt

#fix dns
device_ip=$(getent hosts ${DEVICE_HOST} | awk '{ print $1 }')
echo "$device_ip $DOMAIN.syncloud.info" >> /etc/hosts
echo "$device_ip $APP.$DOMAIN.syncloud.info" >> /etc/hosts

cat /etc/hosts

xvfb-run -l --server-args="-screen 0, 1024x4096x24" py.test -x -s ${TEST_SUITE} --domain=$DOMAIN --app-archive-path=${APP_ARCHIVE_PATH} --device-host=${DEVICE_HOST}