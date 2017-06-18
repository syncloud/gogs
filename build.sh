#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}


export TMPDIR=/tmp
export TMP=/tmp

NAME=gogs
COIN_CACHE_DIR=${DIR}/coin.cache
ARCH=$(uname -m)
GOGS_VERSION=0.11.4
ARCH=$1
VERSION=$2


if [ "${ARCH}" == 'x86_64' ]; then
    GOGS_ARCH=linux_amd64
else
    GOGS_ARCH=raspi2_armv6
fi

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

DOWNLOAD_URL=http://artifact.syncloud.org/3rdparty

coin --to ${BUILD_DIR} raw https://dl.gogs.io/${GOGS_VERSION}/${GOGS_ARCH}.zip --takefolder gogs
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/postgresql-${ARCH}.tar.gz
coin --to ${BUILD_DIR} --ignore-cache raw ${DOWNLOAD_URL}/git-${ARCH}.tar.gz

cp -r ${DIR}/hooks ${BUILD_DIR}
cp -r ${DIR}/config ${BUILD_DIR}/config.templates

mkdir ${BUILD_DIR}/META
echo ${NAME} >> ${BUILD_DIR}/META/app
echo ${VERSION} >> ${BUILD_DIR}/META/version

chmod +x ${BUILD_DIR}/gogs/gogs

echo "zipping"
rm -rf ${NAME}*.tar.gz
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}