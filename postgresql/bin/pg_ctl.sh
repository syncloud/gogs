#!/bin/bash -e
LIBS=${DIR}/usr/local/lib
LIBS=$LIBS:${DIR}/lib
LIBS=$LIBS:${DIR}/usr/lib
exec ${DIR}/lib/ld-*.so* --library-path $LIBS ${DIR}/usr/local/bin/pg_ctl "$@"
