#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
LIBS=$(echo ${DIR}/lib/*linux*/)
LIBS=$LIBS:$(echo ${DIR}/usr/lib/*linux*)
export LD_LIBRARY_PATH=$LIBS
exec ${DIR}/usr/lib/postgresql/*/bin/pg_ctl "$@"
