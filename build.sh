#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$2" ]]; then
    echo "usage $0 name version"
    exit 1
fi

export TMPDIR=/tmp
export TMP=/tmp

NAME=$1
ARCH=$(uname -m)
GOGS_VERSION=0.11.43
VERSION=$2

if [ "${ARCH}" == 'x86_64' ]; then
    GOGS_ARCH=linux_amd64
else
    GOGS_ARCH=raspi2_armv6
fi

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}
mkdir ${BUILD_DIR}/lib

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/git-${ARCH}.tar.gz
tar xf git-${ARCH}.tar.gz
mv git ${BUILD_DIR}
wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/postgresql-${ARCH}.tar.gz
tar xf postgresql-${ARCH}.tar.gz
mv postgresql ${BUILD_DIR}
wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/python-${ARCH}.tar.gz
tar xf python-${ARCH}.tar.gz
mv python ${BUILD_DIR}

${BUILD_DIR}/python/bin/pip install -r ${DIR}/requirements.txt

#use binaries
#coin --to ${BUILD_DIR} raw https://dl.gogs.io/${GOGS_VERSION}/${GOGS_ARCH}.zip --takefolder gogs
#chmod +x ${BUILD_DIR}/gogs/gogs

# or compile
export GOROOT=/tools/go-1.7.6
export PATH=${GOROOT}/bin:$PATH

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

mkdir ${BUILD_DIR}/META
echo ${NAME} >> ${BUILD_DIR}/META/app
echo ${VERSION} >> ${BUILD_DIR}/META/version

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

PACKAGE=${NAME}_${VERSION}_${ARCH}.snap
echo ${PACKAGE} > ${DIR}/package.name
mksquashfs ${SNAP_DIR} ${DIR}/${PACKAGE} -noappend -comp xz -no-xattrs -all-root
