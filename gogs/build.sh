#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
BUILD_DIR=${DIR}/../build/snap

mkdir -p ${BUILD_DIR}/app
mkdir -p ${BUILD_DIR}/bin
mkdir -p ${BUILD_DIR}/lib

cp -r /app/gogs ${BUILD_DIR}/app/
cp -r /lib/. ${BUILD_DIR}/lib/
mkdir -p ${BUILD_DIR}/usr/lib
cp -r /usr/lib/. ${BUILD_DIR}/usr/lib/
cp ${DIR}/bin/gogs.sh ${BUILD_DIR}/bin/gogs

apk add --no-cache patchelf
MUSL_INTERP=$(basename $(ls /lib/ld-musl-*.so.1))
patchelf \
    --set-interpreter /snap/gogs/current/lib/${MUSL_INTERP} \
    --set-rpath /snap/gogs/current/lib:/snap/gogs/current/usr/lib \
    ${BUILD_DIR}/app/gogs/gogs
