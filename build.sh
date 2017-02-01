#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp

NAME=gogs
COIN_CACHE_DIR=${DIR}/coin.cache
ARCH=$(dpkg-architecture -qDEB_HOST_GNU_CPU)
GOGS_VERSION=0.9.128
if [ ! -z "$1" ]; then
    ARCH=$1
fi

VERSION="local"
if [ ! -z "$2" ]; then
    VERSION=$2
fi

if [ "${ARCH}" == 'x86_64' ]; then
    GOGS_ARCH=amd64
fi
if [ "${ARCH}" == 'armv7l' ]; then
    GOGS_ARCH=armv6
fi

GOGS_FILENAME=gogs_v${GOGS_VERSION}_linux_${GOGS_ARCH}.zip

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

DOWNLOAD_URL=http://build.syncloud.org:8111/guestAuth/repository/download

coin --to ${BUILD_DIR} raw https://dl.gogs.io/${GOGS_FILENAME} --takefolder gogs
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_postgresql_${ARCH}/lastSuccessful/postgresql-${ARCH}.tar.gz
coin --to ${BUILD_DIR} --ignore-cache raw ${DOWNLOAD_URL}/thirdparty_git_${ARCH}/lastSuccessful/git-${ARCH}.tar.gz

cp -r ${DIR}/hooks ${BUILD_DIR}
cp -r ${DIR}/config ${BUILD_DIR}/config.templates

mkdir ${BUILD_DIR}/META
echo ${NAME} >> ${BUILD_DIR}/META/app
echo ${VERSION} >> ${BUILD_DIR}/META/version

echo "zipping"
rm -rf ${NAME}*.tar.gz
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}