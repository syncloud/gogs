#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}


export TMPDIR=/tmp
export TMP=/tmp

NAME=gogs
COIN_CACHE_DIR=${DIR}/coin.cache
ARCH=$(uname -m)
GOGS_VERSION=0.11.34
VERSION=$1
INSTALLER=$2

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
coin --to ${BUILD_DIR}/lib py https://pypi.python.org/packages/23/b2/0fa8a4de78475159ea686cf9b3416d1d03d822cadf16fb8866ae35887c0d/syncloud-lib-38.tar.gz#md5=88610aa15d0306c198081a5310726504

coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/postgresql-${ARCH}.tar.gz
coin --to ${BUILD_DIR} --ignore-cache raw ${DOWNLOAD_URL}/git-${ARCH}.tar.gz

#use binaries
#coin --to ${BUILD_DIR} raw https://dl.gogs.io/${GOGS_VERSION}/${GOGS_ARCH}.zip --takefolder gogs
#chmod +x ${BUILD_DIR}/gogs/gogs

# or compile
export PATH=/usr/lib/go-1.6/bin:$PATH

export GOPATH=$(pwd)
mkdir -p $GOPATH/src/github.com/gogits
cd $GOPATH/src/github.com/gogits
wget https://github.com/gogits/gogs/archive/v${GOGS_VERSION}.tar.gz --progress dot:giga -O gogs-${GOGS_VERSION}.tar.gz
tar xf gogs-${GOGS_VERSION}.tar.gz
mv gogs-${GOGS_VERSION} gogs
cd gogs
ls -la
#cp ${DIR}/hacks/pkg/auth/ldap/ldap.go pkg/auth/ldap/ldap.go
go build 
mkdir ${BUILD_DIR}/gogs
cp gogs ${BUILD_DIR}/gogs/
chmod +x ${BUILD_DIR}/gogs/gogs
cp -r templates ${BUILD_DIR}/gogs/
cp -r public ${BUILD_DIR}/gogs/

cp -r ${DIR}/bin ${BUILD_DIR}
cp -r ${DIR}/hooks ${BUILD_DIR}
cp -r ${DIR}/config ${BUILD_DIR}/config.templates
cp -r ${DIR}/lib ${BUILD_DIR}

mkdir ${BUILD_DIR}/META
echo ${NAME} >> ${BUILD_DIR}/META/app
echo ${VERSION} >> ${BUILD_DIR}/META/version

if [ $INSTALLER == "sam" ]; then

    echo "zipping"
    rm -rf ${NAME}*.tar.gz
    tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}

else

    echo "snapping"
    SNAP_DIR=${DIR}/build/snap
    ARCH=$(dpkg-architecture -q DEB_HOST_ARCH)
    rm -rf ${DIR}/*.snap
    mkdir ${SNAP_DIR}
    cp -r ${BUILD_DIR}/* ${SNAP_DIR}/
    cp -r ${DIR}/snap/meta ${SNAP_DIR}/
    cp ${DIR}/snap/snap.yaml ${SNAP_DIR}/meta/snap.yaml
    echo "version: $VERSION" >> ${SNAP_DIR}/meta/snap.yaml
    echo "architectures:" >> ${SNAP_DIR}/meta/snap.yaml
    echo "- ${ARCH}" >> ${SNAP_DIR}/meta/snap.yaml

    mksquashfs ${SNAP_DIR} ${DIR}/${NAME}_${VERSION}_${ARCH}.snap -noappend -comp xz -no-xattrs -all-root

fi