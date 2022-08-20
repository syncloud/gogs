#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
LIBS=${DIR}/usr/local/lib
LIBS=$LIB:${DIR}/lib
LIBS=$LIB:${DIR}/usr/lib
exec ${DIR}/lib/ld-*.so* --library-path $LIBS ${DIR}/usr/local/bin/initdb "$@"
