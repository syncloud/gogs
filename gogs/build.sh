#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
BUILD_DIR=${DIR}/../build/snap

mkdir -p ${BUILD_DIR}/app
mkdir -p ${BUILD_DIR}/bin
mkdir -p ${BUILD_DIR}/lib

cp -r /app/gogs ${BUILD_DIR}/app/
mv ${BUILD_DIR}/app/gogs/gogs ${BUILD_DIR}/app/gogs/gogs.bin
cp -r /lib/. ${BUILD_DIR}/lib/
mkdir -p ${BUILD_DIR}/usr/lib
cp -r /usr/lib/. ${BUILD_DIR}/usr/lib/
cp ${DIR}/bin/gogs.sh ${BUILD_DIR}/bin/gogs
cp ${DIR}/app/gogs.sh ${BUILD_DIR}/app/gogs/gogs
chmod +x ${BUILD_DIR}/app/gogs/gogs
