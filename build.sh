#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}


export TMPDIR=/tmp
export TMP=/tmp

NAME=gogs
COIN_CACHE_DIR=${DIR}/coin.cache
ARCH=$(uname -m)
GOGS_VERSION=0.11.19
VERSION=$1


if [ "${ARCH}" == 'x86_64' ]; then
    GOGS_ARCH=linux_amd64
else
    GOGS_ARCH=raspi2_armv6
fi

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}
mkdir ${BUILD_DIR}/lib

DOWNLOAD_URL=http://artifact.syncloud.org/3rdparty

coin --to ${BUILD_DIR}/lib py https://pypi.python.org/packages/2.7/b/beautifulsoup4/beautifulsoup4-4.4.0-py2-none-any.whl
coin --to ${BUILD_DIR}/lib py https://pypi.python.org/packages/ea/03/92d3278bf8287c5caa07dbd9ea139027d5a3592b0f4d14abf072f890fab2/requests-2.11.1-py2.py3-none-any.whl#md5=b4269c6fb64b9361288620ba028fd385
coin --to ${BUILD_DIR}/lib py https://pypi.python.org/packages/f3/94/67d781fb32afbee0fffa0ad9e16ad0491f1a9c303e14790ae4e18f11be19/requests-unixsocket-0.1.5.tar.gz#md5=08453c8ef7dc03863ff4a30b901e7c20

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