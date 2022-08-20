#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export LANG="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
LIBS=$(echo ${DIR}/lib/*linux*/)
LIBS=$LIBS:$(echo ${DIR}/usr/lib/*linux*)
exec ${DIR}/lib/*/ld-*.so --library-path $LIBS ${DIR}/usr/lib/postgresql/*/bin/initdb "$@"
