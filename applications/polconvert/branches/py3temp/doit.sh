#!/bin/bash
[ -n "$DIFXROOT" ] || {
    echo you need to source setup first
    exit 1
}
svn=`dirname $DIFXROOT`/difx-svn
cd bld=${DIFXROOT/root/bld}
$svn/setup/install-difx \
    --doonly polconvert --newver=polconvert:branches/py3temp --nodoc
ls -l $DIFXROOT/share/polconvert | head -3
ls -l $DIFXROOT/share/hops -3
