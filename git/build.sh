#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )

BUILD_DIR=${DIR}/../build/snap/git

mkdir -p ${BUILD_DIR}/bin
cp -r /usr ${BUILD_DIR}
cp -r /lib ${BUILD_DIR}
cp ${DIR}/bin/* ${BUILD_DIR}/bin/
