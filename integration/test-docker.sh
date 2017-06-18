#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

if [ "$#" -lt 9 ]; then
    echo "usage $0 redirect_user redirect_password redirect_domain app_archive_path installer_version release [all|test_suite] [sam|snapd] device_host"
    exit 1
fi

APP_ARCHIVE_PATH=$(realpath "$4")
INSTALLER_VERSION=$5
RELEASE=$6
TEST=$7
INSTALLER=$8
DEVICE_HOST=$9

GECKODRIVER=0.14.0
FIREFOX=52.0

cd ${DIR}

echo ${APP_ARCHIVE_PATH}

if [ "$TEST" == "all" ]; then
    TEST_SUITE="verify.py test-ui.py"
else
    TEST_SUITE=${TEST}.py
fi

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

sshpass -p syncloud scp -o StrictHostKeyChecking=no install-${INSTALLER}.sh root@${DEVICE_HOST}:/installer.sh

sshpass -p syncloud ssh -o StrictHostKeyChecking=no root@${DEVICE_HOST} /installer.sh ${INSTALLER_VERSION} ${RELEASE}

pip2 install -r ${DIR}/../src/dev_requirements.txt

coin --to ${DIR} raw --subfolder geckodriver https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER}/geckodriver-v${GECKODRIVER}-linux64.tar.gz
coin --to ${DIR} raw https://ftp.mozilla.org/pub/firefox/releases/${FIREFOX}/linux-x86_64/en-US/firefox-${FIREFOX}.tar.bz2
curl https://raw.githubusercontent.com/mguillem/JSErrorCollector/master/dist/JSErrorCollector.xpi -o  JSErrorCollector.xpi

xvfb-run -l --server-args="-screen 0, 1024x4096x24" py.test -x -s ${TEST_SUITE} --email=$1 --password=$2 --domain=$3 --app-archive-path=${APP_ARCHIVE_PATH} --installer=${INSTALLER} --device-host=${DEVICE_HOST}