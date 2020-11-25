#!/usr/bin/python
#
# Script to run PolConvert in Solve mode for non-ALMA case.
# Derived from POLCONVERT_EVN script.
#
# This script has similar machinery to that of drivepolconvert/runpolconvert
# but does not rely on a "runpolconvert" script, and thus is self-contained.
#
from __future__ import absolute_import
import pickle as pk

import argparse
import datetime
import glob
import os
import re
import stat
import sys
import threading
import time
# not needed
# from six.moves import range

# runpolconvert.py is actually in $DIFXROOT/share/polconvert
# rather than on PYTHONPATH since it is not meant to be run
# that way.  It is simpler to stash drivepclib.py in the same
# place for similiar reasons.  Likewise, there is an import
# in drivepolconvert that is enabled to allow drivepclib to
# call back to functions in this file.  See Kluge in Makefile.am
rcpath = 'path not defined'
try:
    rcpath = os.environ['DIFXROOT'] + '/share/polconvert'
    sys.path.insert(0, rcpath)
    import drivepclib as dpc
except Exception as ex:
    print('Exception was',str(ex))
    print('Unable to import drivepclib functionality from:')
    print(rcpath)
    print('This is some sort of build issue you will have to solve.')
    sys.exit(1)

def parseOptions():
    '''
    This script uses its arguments to set up an invocation of PolConvert
    to derive suitable calibrations for a VLBI antenna with linear feeds
    to allow subsequent conversion from mixed-pol calibration products to
    circular basis calibration products.

    It estimates XY-phase, X/Y amplitude ratio, and X-Y multiband delay,
    from a scan on one strong calibrator.  The resulting calibrations
    may be used in a subsequent execution of drivepolconvert to complete
    the circularization process.  This script accepts multiple calibration
    scans (and runs them in parallel, see -P option).

    No script yet exists to collate output products, so your only option
    at present is to try them and see what works best.
    '''
    des = parseOptions.__doc__
    epi = ''
    use = '%(prog)s [options] [input_file [...]]\n  Version'
    use += '$Id$'
    parser = argparse.ArgumentParser(epilog=epi, description=des, usage=use)
    primary = parser.add_argument_group('Primary Options')
    secondy = parser.add_argument_group('Secondary Options')
    ### develop = parser.add_argument_group(
    ###    'Development Options (that may disappear some day)')
    # essential options
    primary.add_argument('-v', '--verbose', dest='verb',
        default=False, action='store_true',
        help='be chatty about the work')
    primary.add_argument('-r', '--run', dest='run',
        default=False, action='store_true',
        help='execute CASA with the generated input')
    primary.add_argument('-l', '--label', dest='label',
        default='', metavar='STRING',
        help='prefix with which to label output calibrations')
    # not normally needed, secondary arguments
    secondy.add_argument('-P', '--parallel', dest='parallel',
        default=6, metavar='INT', type=int,
        help='Number of jobs to run in parallel. '
        '(The default is 6.)')
    secondy.add_argument('-p', '--prep', dest='prep',
        default=False, action='store_true',
        help='run prepolconvert.py on the same joblist--'
        'generally not a good idea unless you are certain it will work')
    secondy.add_argument('-a', '--ant', dest='ant',
        default=1, metavar='INT', type=int,
        help='1-based index of linear (ALMA) antenna (normally 1)')
    secondy.add_argument('-L', '--lin', dest='lin',
        default='AA', metavar='SC', # 'alma'
        help='2-letter station code (all caps) for linear pol station (AA)')
    secondy.add_argument('-I', '--indices', dest='indices',
        default='ZOOM', metavar='INDICES',
        help='comma-sep list of indices or index ranges (this-that, '
        'inclusive) or ZOOM to do find all zoom channels (such as is '
        'done for the ALMA case)')
    secondy.add_argument('-S', '--sites', dest='sites',
        default='', metavar='LIST',
        help='comma-sep list of 2-letter station codes (Xx,Yy,...) to try'
            ' (in this order) to use as a reference antenna')
    secondy.add_argument('-s', '--solve', dest='solve',
        default=1000.0, metavar='FLOAT', type=float,
        help='doSolve argument: for the chi^2 minimizer function which is '
            'computed as sum[ dosolve*(RR/LL-1)^2 + (RL^2 + LR^2) ].  If '
            'doSolve == 0 you minimize the cross-hands; if doSolve >> 1, '
            'you are assuming negligible Stokes V.')
    # the remaining arguments provide the list of input files
    parser.add_argument('nargs', nargs='*',
        help='List of DiFX input job files to process')
    return parser.parse_args()

def parseInputIndices(o):
    '''
    Parse input index list into a doIFs argument string.
    Input should be a comma-sep list of indices or this-that (inclusive).
    '''
    o.doIF = list()
    parts = o.indices.split(',')
    for pp in parts:
        if '-' in pp:
            this,that = pp.split('-')
            o.doIF.append(list(range(int(this),int(this)+int(that)+1)))
        else:
            o.doIF.append(int(pp))
    if o.verb: print('Working with indices',str(o.doIF))

def getInputTemplate(o):
    '''
    This is the input script with %-able adjustments.
    It is similar to what is done in drivepolconvert except
    that we cut out the middle-man (runpolconvert) for one
    less layer of obfuscation.
    '''
    template='''    #!/usr/bin/python
    # This file contains python commands that may either be fed
    # directly to CASA as standard input, or else cut&pasted into
    # the interactive CASA prompts (which you should do if you
    # are having trouble or wish to see some of the plots).
    #
    import re
    %sprint('Debug data follows')
    '''
    # found this via inspect...
    for key,val in o._get_kwargs():
        if type(val) is str or type(val) is datetime.datetime:
            template += ('\n    print("debug: %12s = ","%s")' % (key,val))
        else:   # str(val) is acceptable to print
            template += ('\n    print("debug: %12s = ", %s )' % (key,val))
    template += '''
    print('If Polconvert was loaded a short description follows:')
    print(polconvert.__doc__[0:200],'...')
    %sprint('Real command assembly follows:')
    nargs   = '%s'
    joblist =  %s
    caldir  = '%s'
    workdir = '%s'
    label   = '%s'
    # as with to runpolconvert, we set and copy defaults from polconvert.xml:
    theJob  = joblist[0]
    print('theJob is',theJob, 'nargs is',nargs)
    DiFXinput  = '%%s/%%s' %% (caldir, nargs)
    DiFXoutput = '%%s' %% (re.sub(r'.input$', '.difx', DiFXinput))
    DiFXcalc   = '%%s' %% (re.sub(r'.input$', '.calc', DiFXinput))
    print('DiFXinput is', DiFXinput)
    print('DiFXoutput is', DiFXoutput, 'DiFXcalc is', DiFXcalc)
    zfirst=%d
    zfinal=%d
    doIF = list(range(zfirst+1, zfinal+2))
    NIF = len(doIF)
    linAnt = [%d]
    remote_map = %s
    remlistone = re.sub(r'[" \\'\[\]]','',remote_map[0]).split(',')
    remotename = %s
    linAntName = '%s'
    plotAnt = 1 + remlistone.index(remotename[0])
    print('linAnt is', linAnt, '('+linAntName+')', 'plotAnt is', plotAnt)
    Range = []
    aantpath = ''   # ALMA Antenna MS table
    spw = -1        # spectral window to use
    calapphs = ''   # ASDM_CALAPPPHASE table
    calAPPTime = [0.,5.]
    gains = ['NONE']
    XYavgTime = 0.0
    dterm = gains[0]
    amp_norm = 0.0
    # these are dicts on station
    XYadd = {}      # FIXME  additional phase
    XYadd[linAntName] = [0.0 for i in range(NIF)]
    XYdel = {}      # FIXME  additional delay
    XYratio = {}    # FIXME  X/Y amp ratio
    XYratio[linAntName] = [1.0 for i in range(NIF)]
    # IDI_conjugated is irrelevant for SWIN
    plotIF = doIF
    # timeRange = []
    timeRange = [0,0,0,0, 14,0,0,0]   # first 14 days
    npix = 50
    # solveMethod may be 'gradient', 'Levenberg-Marquardt' or 'COBYLA'
    # calstokes is [I,Q,U,V] for the calibrator; I is ignored.
    #
    # the following line is similar to what is in runpolconvert, but
    # we are working read-only for the Solve case with doTest=True
    # sys.environ['POLCONVERTDEBUG'] = 'True'
    print('Running polconvert....')
    print('IDI=',DiFXoutput, 'OUTPUTIDI=',DiFXoutput,
        'DiFXinput=',DiFXinput, 'DiFXcalc=',DiFXcalc,
        'doIF=',doIF,
        'linAntIdx=',linAnt, 'Range=',Range, 'ALMAant=',aantpath, '...')
    CGains = polconvert(IDI=DiFXoutput, OUTPUTIDI=DiFXoutput,
            DiFXinput=DiFXinput, DiFXcalc=DiFXcalc,
            doIF=doIF,
            linAntIdx=linAnt, Range=Range, ALMAant=aantpath,
            spw=spw, calAPP=calapphs, calAPPTime=calAPPTime,
            APPrefant='',
            gains=[gains], interpolation=[],
            gainmode=[], XYavgTime=XYavgTime,
            dterms=[dterm], amp_norm=amp_norm,
            XYadd=XYadd,
            XYdel=XYdel,
            XYratio=XYratio, usePcal=[], swapXY=[False],
            swapRL=False, feedRotation=[],
            IDI_conjugated=True,
            plotIF=plotIF, plotRange=timeRange,
            plotAnt=plotAnt,
            excludeAnts=[], excludeBaselines=[],
            doSolve=%f,
            solint=[1,1],
            doTest=True, npix=npix,
            solveAmp=True,
            solveMethod='gradient', calstokes=[1.,0.,0.,0.], calfield=-1
            ) 
    print('Polconvert finished')
    #
    # polconvert returns the gains and saves it in PolConvert.XYGains.dat
    # we shall make a copy to verify that this is all working correctly.
    #
    if %s:  # gain debug
        import pickle as pk
        if sys.version_info.major < 3:
            ofile = open('PolConvert.XYGains.copy','w')
        else:
            ofile = open('PolConvert.XYGains.copy','wb')
        try:
            pk.dump(CGains,ofile)
        except Exception as ex:
            printMsg(str(ex))
        ofile.close()
    '''
    return template

def createCasaInput(o, joblist, caldir, workdir):
    '''
    This function creates a file of python commands that can be piped
    directly into CASA.  It now only supports parallel execution.
    Note that joblist is now a list with precisely one job:  [job],
    caldir is '..', and workdir is where we cd'd to for the work.
    '''
    oinput = workdir + '/' + o.input
    if o.verb: print('Creating CASA input file\n  ' + oinput)
    if o.verb: verb = ''
    else:      verb = '#'
    template = getInputTemplate(o)
    # remember to keep the next two statements synchronized!
    print('  .' +verb+verb+ '.\n',
        '  ',o.nargs[0], str(joblist), caldir, workdir, '\n',
        '  ',o.label, o.zfirst, o.zfinal, o.ant, '\n',
        '  ',o.remote_map, o.remotename, o.lin, '\n',
        '  ',o.solve, 'True')
    script = template % (verb, verb,
        o.nargs[0], str(joblist), caldir, workdir,
        o.label, o.zfirst, o.zfinal, o.ant,
        o.remote_map, o.remotename, o.lin,
        o.solve, 'True')
    # write the file, stripping indents
    ci = open(oinput, 'w')
    for line in script.split('\n'):
        ci.write(line[4:] + '\n')
    ci.close()
    return os.path.exists(oinput)

def compatChecks(o):
    '''
    In order to re-use drivepolconvert code, we need to define a
    few things that are set in some of the developmental arguments.
    '''
    o.exp = ''
    o.input = ''
    o.output = ''
    o.remote = -1
    o.xyadd = ''
    o.test = False

def checkOptions(o):
    '''
    Check that all options make sense, and other startup items.
    We do this prior to any real work, but after tarball extraction
    if such was provided.  The subfunctions throw exceptions on issues.
    '''
    compatChecks(o)
    dpc.inputRelatedChecks(o)
    dpc.runRelatedChecks(o)

#
# enter here to do the work
#
if __name__ == '__main__':
    opts = parseOptions()
    checkOptions(opts)
    if opts.prep:
        runPrePolconvert(opts)
    if opts.indices == 'ZOOM':
        dpc.deduceZoomIndices(opts)
    else:
        parseInputIndices(opts)
    # run the jobs in parallel
    if opts.verb:
        print('\nParallel execution with %d threads\n' % opts.parallel)
    dpc.createCasaInputParallel(opts)
    dpc.executeCasaParallel(opts)
    if opts.verb:
        print('\nDrivePolconvert execution is complete\n')
    # explicit 0 exit
    sys.exit(0)

#
# eof
#

#
# Original scripting follows...
#
REFANT = 4 # Antenna to which refer the conversion gain solution (O8)
LINANT = 2 # Antenna with linear feed (EB)
REF_IDI = 'eo014_1_1.IDI6' # IDI with calibrator scan
CALRANGE = [0,23,28,0,0,23,39,45] # time range of calibrator scan (J0927+3902)
NCHAN = 32 # Number of channels per IF (to compute the multi-band delay)
NIF = 8  # Number of IFs.
NITER = 1  # Number of X-Y phase-estimate iterations (just 1 should suffice)
# List with the names of all FITS-IDIs to convert:
ALL_IDIs = ['eo014_1_1.IDI6']
import os
import numpy as np
# Initial gain estimates (dummy gains):
EndGainsAmp = [1.0 for i in range(NIF)]
EndGainsPhase = [0.0 for i in range(NIF)]
TotGains = []
# Estimate cross-gains with PolConvert:
for i in range(NITER):
##################################
# Convert XYadd and XYratio to lists, in order
# to avoid corruption of the *.last file
  if i==0:
    XYadd = [EndGainsPhase]
    XYratio = [EndGainsAmp]
  else:
    XYadd = [[list(ll) for ll in EndGainsPhase]]
    XYratio = [[list(ll) for ll in EndGainsAmp]]
##################################
  polconvert(IDI=REF_IDI,
             OUTPUTIDI=REF_IDI,
             linAntIdx=[LINANT],
             plotIF = [],
             doIF = [],
             XYadd = XYadd,
             XYratio = XYratio,
             Range = CALRANGE,
             plotRange = CALRANGE,
             IDI_conjugated = False,
             doSolve = 1000.,   #4,
             solint = [1,1],  #BP MODE
             plotAnt = REFANT,
             amp_norm = 0.0,
             solveMethod = 'COBYLA',
             excludeAnts = [8,9],
             doTest=True)
  
  ifile = open('PolConvert.XYGains.dat')
  GainsIt = pk.load(ifile)
  ifile.close()
  TotGains.append(GainsIt)
  for k in range(NIF):
    EndGainsAmp[k] = EndGainsAmp[k]*np.array(GainsIt['XYratio'][LINANT][k])
    EndGainsPhase[k] = EndGainsPhase[k] + np.array(GainsIt['XYadd'][LINANT][k])
  os.system('rm -rf FRINGE.PLOTS.ITER%i'%i)
  os.system('mv FRINGE.PLOTS FRINGE.PLOTS.ITER%i'%i)
  os.system('mv Cross-Gains.png Cross-Gains.ITER%i.png'%i)


# Add this suffix to the converted IDIs (empty string -> overwrite!)
SUFFIX = '.POLCONVERT'
# HERE WE CAN CONVERT ALL IDIs:
if False:
 XYadd = [[list(ll) for ll in EndGainsAmp]]
 XYratio = [[list(ll) for ll in EndGainsPhase]]

 for IDI in ALL_IDIs:
  polconvert(IDI=IDI,
             OUTPUTIDI=IDI+SUFFIX,
             linAntIdx=[LINANT],
             plotIF = [],
             XYadd = [list(Phases)],
             XYdel = [multiBand],
             IDI_conjugated = False,
             XYratio = [AmpRat],
             amp_norm = 0.0,
             doTest=False)
