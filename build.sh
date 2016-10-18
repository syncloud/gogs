#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp

NAME=gogs
NEXTCLOUD_VERSION=10.0.0
COIN_CACHE_DIR=${DIR}/coin.cache
ARCH=$(dpkg-architecture -qDEB_HOST_GNU_CPU)
if [ ! -z "$1" ]; then
    ARCH=$1
fi

VERSION="local"
if [ ! -z "$2" ]; then
    VERSION=$2
fi

if [ "${ARCH}" == 'x86_64' ]; then
    GOGS_FILENAME="gogs_v0.9.97_linux_386.zip"
fi
if [ "${ARCH}" == 'armv7l' ]; then
    GOGS_FILENAME="gogs_v0.9.97_linux_arm.zip"
fi

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

coin --to ${BUILD_DIR} raw https://dl.gogs.io/${GOGS_FILENAME} --takefolder gogs

cp -r ${DIR}/bin ${BUILD_DIR}
cp -r ${DIR}/config ${BUILD_DIR}/config.templates

mkdir ${BUILD_DIR}/META
echo ${NAME} >> ${BUILD_DIR}/META/app
echo ${VERSION} >> ${BUILD_DIR}/META/version

echo "zipping"
rm -rf ${NAME}*.tar.gz
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}