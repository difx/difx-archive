[ -n "$DIFXROOT" ] || {
    echo you need to source setup first
    exit 1
}
svn=`dirname $DIFXROOT`/difx-svn
$svn/setup/install-difx \
    --doonly polconvert --newver=polconvert:branches/py3temp --nodoc
ls -l $DIFXROOT/share/polconvert
ls -l $DIFXROOT/share/hops
