#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}
apt update
apt install -y libltdl7 libnss3
APP=git
BUILD_DIR=${DIR}/../build/snap/$APP
docker ps -a -q --filter ancestor=$APP:syncloud --format="{{.ID}}" | xargs docker stop | xargs docker rm || true
docker rmi $APP:syncloud || true
docker build -t $APP:syncloud .
docker create --name=$APP $APP:syncloud
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
docker export $APP -o app.tar
docker ps -a -q --filter ancestor=$APP:syncloud --format="{{.ID}}" | xargs docker stop | xargs docker rm || true
docker rmi $APP:syncloud || true
tar xf app.tar
rm -rf app.tar
mv ${BUILD_DIR}/usr/bin/git ${BUILD_DIR}/usr/bin/git.bin
mv ${BUILD_DIR}/usr/bin/git-lfs ${BUILD_DIR}/usr/bin/git-lfs.bin
mv ${BUILD_DIR}/usr/bin/git-shell ${BUILD_DIR}/usr/bin/git-shell.bin
mv ${BUILD_DIR}/usr/bin/git-receive-pack ${BUILD_DIR}/usr/bin/git-receive-pack.bin
mv ${BUILD_DIR}/usr/bin/git-upload-pack ${BUILD_DIR}/usr/bin/git-upload-pack.bin
mv ${BUILD_DIR}/usr/bin/git-upload-archive ${BUILD_DIR}/usr/bin/git-upload-archive.bin
cp ${DIR}/bin/* ${BUILD_DIR}/bin
