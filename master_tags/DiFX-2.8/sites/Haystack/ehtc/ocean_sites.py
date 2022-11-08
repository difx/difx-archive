#!/usr/bin/env python
#
# Script to rip through a VEX file and generate input for 
# the ocean loading catalog.
'''
    This script takes one argument (a vex.obs) and rips through
    to collect station positions in a format suitable for input
    to the calculator at http://holt.oso.chalmers.se/loading/:

    go to http://holt.oso.chalmers.se/loading/
    select 'TPXO.7.2'
    select 'vertical and horizontal displacements'
    select 'NO' for centre of mass motion
    choose 'BLQ' output
    Enter site name, X, Y, Z (meters)
    Format (A8,16X,1X,3F16.3), X,Y,Z left justified as below:

    MADRID64                      4849092.701     -360180.778     4115108.983

    For difxcalc usage, edit the output to add the 2-digit code in
    columns 13-14 of the line that contains the station name.  E.g.
    when done, the 11 lines for ALMA might look like this:

      ALMA      AA
    $$ Complete TPXO.7.2
    $$ Computed by OLFG, H.-G. Scherneck, Onsala Space Observatory 2017-Oct-30
    $$ ALMA,                      RADI TANG  lon/lat:  292.2453  -23.0292 5070.371
      .00292 .00128 .00117 .00027 .00460 .00304 .00146 .00059 .00027 .00016 .00017
      .00259 .00055 .00054 .00018 .00151 .00093 .00047 .00017 .00007 .00003 .00004
      .00117 .00046 .00029 .00014 .00096 .00081 .00030 .00017 .00011 .00005 .00003
        95.6   78.0   97.1   87.3 -138.0 -156.2 -140.0 -166.3 -147.8 -162.3 -176.7
        36.2   73.5    9.8   59.9   35.5  -14.0   32.4  -45.7  104.3   63.5    8.4
        52.3   99.8   23.8   97.9  106.1   75.7  101.4   56.8  177.8  177.2  177.4
    $$

    (the above example has the original 2017 position).  Note that newer
    models are available:  TPXO.9.5a, TPXO.9.2a, TPXO.9-Atlas.

    If a second argument is present and contains '@' (i.e. is a valid email address),
    the output will be formatted to a file ocean-request.txt that may be sent with

    sendmail -t < ocean-request.txt

    You may need/want to review/edit the request file.  (And this only works
    on a system where sendmail is installed....)
'''

from __future__ import absolute_import
from __future__ import print_function
import os
import re
import sys
from six.moves import map

def grok(vex):
    '''
    Look for SITE = and site_position = and return result
        ref $SITE = ...;
        site_position = ...;
    Not fully robust against anything stupid in the vex file.
    '''
    fv = open(vex)
    blck_re = re.compile(r'^\$SITE;')
    site_re = re.compile(r'^\s*site_name\s+=' +
        '\s*([^;]+);')
    spos_re = re.compile(r'^\s*site_position\s*=' +
        '\s*([-0-9.+]+)\s*m:\s*([-0-9.+]+)\s*m:\s*([-0-9.+]+)\s*m;')
    answers = {}
    station = None
    inside = False
    for liner in fv.readlines():
        line = liner.rstrip()
        if len(line) == 0: continue
        blck_hit = blck_re.search(line)
        if blck_hit:
            inside = True
            continue;
        if inside:
            site_hit = site_re.search(line)
            if site_hit:
                station = site_hit.group(1)
            spos_hit = spos_re.search(line)
            if spos_hit:
                answers[station] = list(map(float, [
                    spos_hit.group(1), spos_hit.group(2), spos_hit.group(3)]))
            if line[0] == '$':
                inside = False
    fv.close()
    return answers


# main entry point
if __name__ == '__main__':
    vex = None
    elm = None
    try:
      vex = sys.argv[1]
      if vex == 'help' or vex == '--help' or not os.path.exists(vex):
          raise Exception(__doc__)
    except:
        if vex == None or vex == 'help' or vex == '--help':
            print(__doc__)
        elif not os.path.exists(vex) or len(sys.argv) < 2:
            print('a vex file is required, try --help')
        sys.exit(1)
    print('//', vex)
    nxyz = grok(vex)
    if len(sys.argv) == 3 and '@' in sys.argv[2]:
        elm = sys.argv[2]
        f = open('ocean-request.txt', 'w')
        f.write('To: loading@holt.oso.chalmers.se\n')
        f.write('From : ' + elm + '\n')
        f.write('Subject: Ocean Loading Tides\n')
        f.write('fromaddress = Ocean Loading Tides\n')
        f.write('Header = ---- Ocean loading values follow next: ----\n')
        f.write('Model = TPXO.7.2\n')
        f.write('LoadingType = displacement\n')
        f.write('GreensF = mc00egbc\n')
        f.write('CMC = 0\n')
        f.write('Plot = 0\n')
        f.write('OutputFormat = BLQ\n')
        f.write('Stations = ')
        for station in sorted(nxyz.keys()):
            f.write("%-24s %15.3f %15.3f %15.3f\n" % (
                station, nxyz[station][0], nxyz[station][1], nxyz[station][2]))
        f.write('\n')
        f.write('MyEmail = %s\n' % elm)
        f.write('ReplyTo = %s\n' % elm)
        f.write('-------------------------------------------------------------------\n')
        f.close()
    else:
        for station in sorted(nxyz.keys()):
            print("%-24s %15.3f %15.3f %15.3f" % (
                station, nxyz[station][0], nxyz[station][1], nxyz[station][2]))

#
# eof
#
