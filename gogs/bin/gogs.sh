#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ..  && pwd )

export PATH=$PATH:$DIR/bin
LIBS=${DIR}/lib:${DIR}/usr/lib
${DIR}/lib/ld-musl-*.so* --argv0 /snap/gogs/current/app/gogs/gogs --library-path $LIBS ${DIR}/app/gogs/gogs.bin "$@"
