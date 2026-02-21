#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
SNAP_DIR=$( cd "$DIR/../.." && pwd )
exec $SNAP_DIR/lib/ld-musl-*.so* --library-path $SNAP_DIR/lib:$SNAP_DIR/usr/lib $DIR/gogs.bin "$@"
