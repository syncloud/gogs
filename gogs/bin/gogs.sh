#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ..  && pwd )

export PATH=$PATH:$DIR/bin
LIBS=${DIR}/lib
${DIR}/lib/ld-musl-*.so* --library-path $LIBS ${DIR}/app/gogs/gogs "$@"
