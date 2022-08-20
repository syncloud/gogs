#!/bin/bash -e
LIBS=${DIR}/usr/local/lib
LIBS=$LIB:${DIR}/lib
LIBS=$LIB:${DIR}/usr/lib
exec ${DIR}/lib/ld-*.so* --library-path $LIBS ${DIR}/usr/local/bin/pg_ctl "$@"
