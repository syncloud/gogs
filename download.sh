#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
DOWNLOAD_URL=https://github.com/syncloud/3rdparty/releases/download
GOGS_VERSION=0.11.43
ARCH=$(uname -m)
rm -rf ${DIR}/build
BUILD_DIR=${DIR}/build/snap
mkdir -p ${BUILD_DIR}

cd ${DIR}/build

apt update
apt -y install wget unzip

wget --progress=dot:giga ${DOWNLOAD_URL}/nginx/nginx-${ARCH}.tar.gz
tar xf nginx-${ARCH}.tar.gz
mv nginx ${BUILD_DIR}

wget --progress=dot:giga ${DOWNLOAD_URL}/git-${ARCH}.tar.gz
tar xf git-${ARCH}.tar.gz
mv git ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/postgresql-${ARCH}.tar.gz
tar xf postgresql-${ARCH}.tar.gz
mv postgresql ${BUILD_DIR}

wget https://github.com/gogits/gogs/archive/v${GOGS_VERSION}.tar.gz --progress dot:giga -O gogs-${GOGS_VERSION}.tar.gz
tar xf gogs-${GOGS_VERSION}.tar.gz
mv gogs-${GOGS_VERSION} gogs
