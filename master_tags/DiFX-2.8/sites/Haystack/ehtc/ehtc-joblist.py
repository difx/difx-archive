--- ehtc-joblist.py	(original)
+++ ehtc-joblist.py	(refactored)
@@ -8,6 +8,8 @@
 Script to parse a joblist and a vex file and produce lists of job numbers
 '''
 
+from __future__ import absolute_import
+from __future__ import print_function
 import argparse
 import glob
 import math
@@ -16,6 +18,8 @@
 import subprocess
 import sys
 import xml.etree.ElementTree
+from six.moves import map
+from six.moves import range
 
 def parseOptions():
     '''
@@ -164,21 +168,21 @@
     epoch *= 60
     secs = int(epoch)
     epoch -= secs
-    if verb: print '%04d %03d %02d %02d %02d  rem %.9f d' % (
-        years, doy, hours, mins, secs, (epoch/86400.0))
+    if verb: print('%04d %03d %02d %02d %02d  rem %.9f d' % (
+        years, doy, hours, mins, secs, (epoch/86400.0)))
     return '%04dy%03dd%02dh%02dm%02ds' % (years, doy, hours, mins, secs)
 
 def doTestVex(vex, verb=False):
     m = vex2MJD(vex)
-    print vex, '->', m
+    print(vex, '->', m)
     v = MJD2Vex(m, verb)
-    print v
+    print(v)
     sys.exit(0)
 def doTestMJD(mjd, verb=False):
     v = MJD2Vex(mjd, verb)
-    print mjd, '->', v
+    print(mjd, '->', v)
     m = vex2MJD(v)
-    print m
+    print(m)
     sys.exit(0)
 
 def parseInputCalc(inp, clc, vrb):
@@ -230,9 +234,9 @@
     fc.close()
     if mjdstart: vexstart = MJD2Vex(mjdstart, vrb)
     vexinfo = [scan,vexstart,mjdstart,sdur,vsrc,mode]
-    if jid != jni or jid != jnc: print '#bogus job',jni,jnc,jid
+    if jid != jni or jid != jnc: print('#bogus job',jni,jnc,jid)
     answer = [mjdstart, mjdstop, list(antenniset), vexinfo]
-    if vrb: print '# ',jid,answer
+    if vrb: print('# ',jid,answer)
     return jid,answer,antenniset
 
 def doInputs(o):
@@ -243,29 +247,29 @@
     o.inputs is non-empty if we were called, but we should check that
     it points to some directory
     '''
-    if o.verb: print '# globbing with:', o.inputs + '_*.input'
+    if o.verb: print('# globbing with:', o.inputs + '_*.input')
     dirn = os.path.dirname(o.inputs)
     if dirn == '':
-        print '# globbing for files in the current working directory'
+        print('# globbing for files in the current working directory')
     else:
         if not os.path.exists(dirn):
-            raise Exception, '-i argument must be set sensibly'
+            raise Exception('-i argument must be set sensibly')
     if o.job == '':
         o.job = os.path.basename(o.inputs)
-        if o.verb: print '# set job to', o.job
+        if o.verb: print('# set job to', o.job)
     o.inptfiles = glob.glob(o.inputs + '_*.input')
     o.calcfiles = glob.glob(o.inputs + '_*.calc')
     if len(o.inptfiles) != len(o.calcfiles):
-        print 'Mismatch in number of input/calc files, bailing'
+        print('Mismatch in number of input/calc files, bailing')
         sys.exit(1)
     if not o.inptfiles:
-        print 'No input files matching pattern %s_*.input found! Stopping' % (
-            o.inputs)
+        print('No input files matching pattern %s_*.input found! Stopping' % (
+            o.inputs))
         sys.exit(1)
-    o.pairs = map(lambda x,y:(x,y), sorted(o.inptfiles), sorted(o.calcfiles))
+    o.pairs = list(map(lambda x,y:(x,y), sorted(o.inptfiles), sorted(o.calcfiles)))
     o.cabbage = {}
     for inp,clc in o.pairs:
-        if o.verb: print '#Input:',inp,'\n#Calc: ',clc
+        if o.verb: print('#Input:',inp,'\n#Calc: ',clc)
         jn,dets,antset = parseInputCalc(inp,clc,o.verb)
         o.antset |= antset
         if dets and jn: o.cabbage[jn] = dets
@@ -283,15 +287,15 @@
     V2DV  = task[5].split('=')[1]
     VEX   = task[6].split('=')[1]
     if o.verb:
-        print '# Job EXPER %s V2D %s PASS %s MJD %s' % (EXPER, V2D, PASS, MJD)
-        print '# DiFX/V2D version is %s/%s' % (VER, V2DV)
-        print '# Vexfile is %s' % VEX
+        print('# Job EXPER %s V2D %s PASS %s MJD %s' % (EXPER, V2D, PASS, MJD))
+        print('# DiFX/V2D version is %s/%s' % (VER, V2DV))
+        print('# Vexfile is %s' % VEX)
     ovp = os.path.abspath(o.vexobs)
     vxp = os.path.abspath(VEX)
     if ovp != vxp and o.verb:
-        print '#Warning, this job file refers to a different vexfile:'
-        print '# ',ovp
-        print '# ',vxp
+        print('#Warning, this job file refers to a different vexfile:')
+        print('# ',ovp)
+        print('# ',vxp)
 
 def doJobList(o):
     '''
@@ -300,7 +304,7 @@
     o.jobbage[#] = [start,stop [antennas]]
     '''
     if not os.path.exists(o.joblist): return
-    if o.verb: print '# examining ',o.joblist
+    if o.verb: print('# examining ',o.joblist)
     f = open(o.joblist)
     first = True
     o.jobbage = {}
@@ -316,13 +320,13 @@
             MSTOP  = float(dets[2])
             ANTENNAS = dets[9:]
             if o.verb:
-                print '#Job %s MJD (%.7f..%.7f) antennas %s' % (
-                    JOBNUM, MSTART, MSTOP, '-'.join(ANTENNAS))
+                print('#Job %s MJD (%.7f..%.7f) antennas %s' % (
+                    JOBNUM, MSTART, MSTOP, '-'.join(ANTENNAS)))
             o.jobbage[JOBNUM] = [MSTART, MSTOP, ANTENNAS]
             for b in ANTENNAS: o.antennaset.add(b)
     f.close()
     if o.verb:
-        print '# Unique antennas: ' + ' '.join(o.antennaset)
+        print('# Unique antennas: ' + ' '.join(o.antennaset))
 
 def doParseVex(o):
     '''
@@ -332,19 +336,19 @@
         o.vxoxml = os.path.basename(o.vexobs[0:-8]) + '.xml'
         args = ['VEX2XML', '-in', o.vexobs, '-out', o.vxoxml]
         if o.verb:
-            print '#Converting VEX to XML with:\n# ' + ' '.join(args)
+            print('#Converting VEX to XML with:\n# ' + ' '.join(args))
         try:
             p = subprocess.Popen(args,
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
-        except Exception, ex:
-            raise Exception, 'VEX2XML failed: ' + str(ex)
+        except Exception as ex:
+            raise Exception('VEX2XML failed: ' + str(ex))
         (v2xout, v2xerr) = p.communicate()
         p.wait()
         if p.returncode:
             err = 'Return code %d from VEX2XML' % p.returncode
-            raise RuntimeError, err
+            raise RuntimeError(err)
     else:
-        raise Exception, 'no file ' + o.vexobs + ' to parse'
+        raise Exception('no file ' + o.vexobs + ' to parse')
     o.vextree = xml.etree.ElementTree.parse(o.vxoxml)
     os.unlink(o.vxoxml)
 
@@ -375,7 +379,7 @@
         sre = scan_re.search(line)
         if sre:
             lastscan = sre.group(1)
-            if o.verb: print 'assigning lastscan', lastscan
+            if o.verb: print('assigning lastscan', lastscan)
             continue
         first = first_re.search(line)
         final = final_re.search(line)
@@ -386,16 +390,16 @@
         if len(thisproj) > 0 and len(lastscan) > 0:
             if thisproj in o.projscans:
                 o.projscans[thisproj].append(lastscan)
-                if o.verb: print 'appending lastscan', lastscan, 'to',thisproj
+                if o.verb: print('appending lastscan', lastscan, 'to',thisproj)
             else:
                 o.projscans[thisproj] = [lastscan]
-                if o.verb: print 'new prj w/lastscan', lastscan, 'to',thisproj
+                if o.verb: print('new prj w/lastscan', lastscan, 'to',thisproj)
             lastscan = ''
         if final: thisproj = 'na'
     f.close()
     if o.verb:
         for p in sorted(o.projscans.keys()):
-            print '# project', p, ': ', o.projscans[p]
+            print('# project', p, ': ', o.projscans[p])
 
 def doFindSrcs(o):
     '''
@@ -411,7 +415,7 @@
         dec   = sd.find('dec/value').text
         frame = sd.find('ref_coord_frame/value').text
         if o.verb:
-            print dname,sname,ra,dec,frame
+            print(dname,sname,ra,dec,frame)
         o.srcs.append(sname)
 
 def doInputSrcs(o):
@@ -457,10 +461,10 @@
         if job:
             dur = 86400.0 * (o.jobbage[job][1] - o.jobbage[job][0])
             if o.verb:
-                print job, name, start, smjd
-                print job,' ', mode, vsrc, int(dur + 0.5), o.jobbage[job][0]
-                print job,' ', o.jobbage[job][2]
-                print job,' ', sits
+                print(job, name, start, smjd)
+                print(job,' ', mode, vsrc, int(dur + 0.5), o.jobbage[job][0])
+                print(job,' ', o.jobbage[job][2])
+                print(job,' ', sits)
             o.jobbage[job].append([name, start, smjd, dur, vsrc, mode])
             o.jobbage[job].append(sits)
         o.vexscans[name] = [name, start, smjd, vsrc, mode]
@@ -507,7 +511,7 @@
     try:
         if   os.environ['uniq'] == 'true':  o.uniq = True
         elif os.environ['uniq'] == 'false': o.uniq = False
-        else: raise Exception, 'Illegal uniq value: ' + os.environ['uniq']
+        else: raise Exception('Illegal uniq value: ' + os.environ['uniq'])
     except:
         pass
     return o
@@ -526,7 +530,7 @@
 	if len(files) > 0:
 	    newjobs[j] = o.rubbage[j]
 	else:
-	    if o.verb: print '# No data in ' + difx + '/*'
+	    if o.verb: print('# No data in ' + difx + '/*')
     o.rubbage = newjobs
 
 def doSelectSource(o):
@@ -535,13 +539,13 @@
     So source is o.jobbage[#][3][4]
     '''
     if o.source == '': return
-    if o.verb: print '# Selecting on source', o.source
+    if o.verb: print('# Selecting on source', o.source)
     newjobs = {}
     if o.source in o.srcs:
         for j in o.rubbage:
             if o.rubbage[j][3][4] == o.source:
                 newjobs[j] = o.rubbage[j]
-                if o.verb: print '#S',j,str(newjobs[j])
+                if o.verb: print('#S',j,str(newjobs[j]))
     o.rubbage = newjobs
 
 def doSelectProject(o):
@@ -550,13 +554,13 @@
     So scan name is o.rubbage[#][3][0]
     '''
     if o.project == '': return
-    if o.verb: print '# Selecting on project', o.project, len(o.projscans)
+    if o.verb: print('# Selecting on project', o.project, len(o.projscans))
     newjobs = {}
     if o.project in o.projscans:
         for j in o.rubbage:
             if o.rubbage[j][3][0] in o.projscans[o.project]:
                 newjobs[j] = o.rubbage[j]
-                if o.verb: print '#P',j,str(newjobs[j])
+                if o.verb: print('#P',j,str(newjobs[j]))
     o.rubbage = newjobs
 
 def bustedCorr(o_inputs, jobnum):
@@ -577,7 +581,7 @@
     '''
     if not o.uniq: return
     if o.rubbage == None or len(o.rubbage) == 0: return
-    if o.verb: print '# Reducing joblist to uniq job set'
+    if o.verb: print('# Reducing joblist to uniq job set')
     scandict = {}
     joblist = sorted(o.rubbage.keys())
     joblist.reverse()
@@ -585,7 +589,7 @@
         job = o.rubbage[j]
         ky = "%s-%s" % (job[3][0], job[3][4])
         if ky in scandict or bustedCorr(o.inputs, j):
-            if o.verb: print '# Discarding duplicate or broken job',j
+            if o.verb: print('# Discarding duplicate or broken job',j)
             del(o.rubbage[j])
             continue
         else:
@@ -606,39 +610,39 @@
     Generate a list of antennas from the joblist file
     '''
     if len(o.antlers) == 0: return
-    print 'antennas="' + ' '.join(o.antlers) + '"'
+    print('antennas="' + ' '.join(o.antlers) + '"')
 
 def doJobInputs(o):
     '''
     Generate a list of job input files from the joblist file
     '''
     if len(o.rubbage) == 0: return
-    jl = map(lambda x:"%s_%s.input" % (o.job, x), sorted(o.rubbage.keys()))
+    jl = ["%s_%s.input" % (o.job, x) for x in sorted(o.rubbage.keys())]
     #print 'jobs="' + ' '.join(sorted(o.rubbage.keys())) + '"'
-    print 'jobs="' + ' '.join(jl) + '"'
+    print('jobs="' + ' '.join(jl) + '"')
 
 def doScans(o):
     '''
     Generate a list of scan numbers
     '''
     if len(o.rubbage) == 0: return
-    js = map(lambda x:o.rubbage[x][3][0], sorted(o.rubbage.keys()))
-    print 'scans="' + ' '.join(js) + '"'
+    js = [o.rubbage[x][3][0] for x in sorted(o.rubbage.keys())]
+    print('scans="' + ' '.join(js) + '"')
 
 def doNumbers(o):
     '''
     Generate a list of job numbers from the joblist file
     '''
     if len(o.rubbage) == 0: return
-    jl = map(lambda x:"%s_%s.input" % (o.job, x), sorted(o.rubbage.keys()))
-    print 'numbers="' + ' '.join(sorted(o.rubbage.keys())) + '"'
+    jl = ["%s_%s.input" % (o.job, x) for x in sorted(o.rubbage.keys())]
+    print('numbers="' + ' '.join(sorted(o.rubbage.keys())) + '"')
 
 def doSources(o):
     '''
     Generate a list of sources from the vex file
     '''
     if len(o.srcs) == 0: return
-    print 'sources="' + ' '.join(o.srcs) + '"'
+    print('sources="' + ' '.join(o.srcs) + '"')
 
 def doProjects(o):
     '''
@@ -646,7 +650,7 @@
     '''
     if len(o.projscans) == 0: return
     for p in o.projscans:
-        print 'project_' + p + '="' + ' '.join(o.projscans[p]) + '"'
+        print('project_' + p + '="' + ' '.join(o.projscans[p]) + '"')
 
 def doReport(o):
     '''
@@ -661,12 +665,12 @@
         for p in o.projscans:
             if scan in o.projscans[p]: proj = p
         antlist = '-'.join(sorted(job[2]))
-        print ('%5s %6s %10s %8s %s' %
-            (j, job[3][0], job[3][4], proj, antlist)),
+        print(('%5s %6s %10s %8s %s' %
+            (j, job[3][0], job[3][4], proj, antlist)), end=' ')
         if antlist[0:2] != 'AA':
-            print '# do not polconvert!'
+            print('# do not polconvert!')
         else:
-            print ''
+            print('')
 
 def doGroups(o, doLabels):
     '''
@@ -693,24 +697,24 @@
     if doLabels:
         #print 'false && { # start with a short job'
         last='zippo'
-        print '# The tests with exit are a reminder to make adjustments above'
+        print('# The tests with exit are a reminder to make adjustments above')
         for a in sorted(list(ans)):
             proj,targ,clss = a.split(':')
             if proj != last and last != 'zippo':
-                print '}'
+                print('}')
             if proj != last:
-                print '[ -z "$QA2_' + proj + '" ] && echo QA2 error && exit 1'
-                print '$QA2_' + proj + ' && {'
-                print '  echo processing QA2_' + proj + ' job block.'
+                print('[ -z "$QA2_' + proj + '" ] && echo QA2 error && exit 1')
+                print('$QA2_' + proj + ' && {')
+                print('  echo processing QA2_' + proj + ' job block.')
             exprt=('  export proj=%s targ=%s class=%s' % tuple(a.split(':')))
-            print  '%-54s    label=%s-%s' % (exprt,proj,targ)
-            print ('  nohup $ehtc/ehtc-jsgrind.sh < /dev/null ' +
-                '> $label-$subv.log 2>&1' )
+            print('%-54s    label=%s-%s' % (exprt,proj,targ))
+            print(('  nohup $ehtc/ehtc-jsgrind.sh < /dev/null ' +
+                '> $label-$subv.log 2>&1' ))
             last = proj
-        print '}'
+        print('}')
     else:
         for a in sorted(list(ans)):
-            print ('export proj=%s targ=%s class=%s' % tuple(a.split(':')))
+            print(('export proj=%s targ=%s class=%s' % tuple(a.split(':'))))
 
 def doLostScans(o):
     '''
@@ -731,11 +735,11 @@
     Provide a report of scans that don't have matching jobs.
     Each scan name has a list: [name, start, smjd, vsrc, mode]
     '''
-    print '### Totally missing scans'
+    print('### Totally missing scans')
     for name in o.lostscans:
-        print 'Missing %s at %s on %s' % (
-            name, o.lostscans[name][1], o.lostscans[name][3])
-    print
+        print('Missing %s at %s on %s' % (
+            name, o.lostscans[name][1], o.lostscans[name][3]))
+    print()
 
 def prodDict(verb, codefile, autos):
     '''
@@ -753,8 +757,8 @@
             sdic[two.upper()] = one
         except:
             pass
-    if verb: print 'station',spol
-    if verb: print 'scodes',sdic
+    if verb: print('station',spol)
+    if verb: print('scodes',sdic)
     # collect in bpol[ref+rem] the number of polarizations correlated
     for ref in spol:
         for rem in spol:
@@ -764,7 +768,7 @@
                     bpol[ref+rem] = spol[ref]
                 else:
                     bpol[ref+rem] = spol[ref]*spol[rem]
-    if verb: print 'baseline',bpol
+    if verb: print('baseline',bpol)
     cf.close()
     return sdic,bpol
 
@@ -773,7 +777,7 @@
     For each baseline work out how many pol products should be present
     and report errors.
     '''
-    if verb: print antennas
+    if verb: print(antennas)
     total = 0
     track = {}
     for reftwo in sorted(antennas):
@@ -783,7 +787,7 @@
             if ref+rem in track or rem+ref in track: continue
             track[ref+rem] = blprodic[ref+rem]
             total += track[ref+rem]
-    if verb: print track
+    if verb: print(track)
     error = ''
     for fringe in sorted(fringes):
         frng = os.path.basename(fringe)
@@ -795,11 +799,11 @@
             track[lb] -= 1
         else:
             error += ' ' + bl + '|' + lb
-    if verb: print track
+    if verb: print(track)
     for bl in track:
         if track[bl] > 0: error += ' ' + bl + ':' + str(track[bl])
         if track[bl] < 0: error += ' ' + bl + '!' + str(track[bl])
-    if verb: print error
+    if verb: print(error)
     return total,error
 
 def doCheck(o):
@@ -819,19 +823,19 @@
         if len(ffdir) == 1:
             ffringes = glob.glob(ffdir[0] + '/' + '??.B.*.*')
             #print jn,scanname,vexstart,antennas,ffdir[0],len(ffringes)
-            print jn,scanname,'have','%3d' % len(ffringes),'fringes,',
+            print(jn,scanname,'have','%3d' % len(ffringes),'fringes,', end=' ')
             if len(o.blproddict) > 0:
                 efrng,edets = calcExpFringes(
                     o.verb, o.scodes, o.blproddict, antennas, ffringes)
-                print '%3d' % efrng,'expected',
+                print('%3d' % efrng,'expected', end=' ')
                 if len(edets) > 0:
-                    print '( missing:',edets,')'
+                    print('( missing:',edets,')')
                 else:
-                    print
+                    print()
             else:
-                print
+                print()
         else:
-            print jn,scanname,'has no 4fit dir'
+            print(jn,scanname,'has no 4fit dir')
 
 def doTiming(o):
     '''
@@ -873,7 +877,7 @@
                 else:
                     timing = 'busted'
             job = pcd.split('.')[0] + ' ...'
-            print job,status,timing,'-'.join(ants)
+            print(job,status,timing,'-'.join(ants))
 
 def updateBLPOL(jobinput, verb):
     '''
@@ -916,7 +920,7 @@
         # create datastream and baseline indices
         ads_hit = ads_re.search(line)
         if ads_hit: 
-            ds_indices = range(int(ads_hit.group(1)))
+            ds_indices = list(range(int(ads_hit.group(1))))
             continue
         dsi_hit = dsi_re.search(line)
         if dsi_hit: 
@@ -924,7 +928,7 @@
             continue
         bls_hit = bls_re.search(line)
         if bls_hit: 
-            bl_indices = range(int(bls_hit.group(1)))
+            bl_indices = list(range(int(bls_hit.group(1))))
             continue
         bli_hit = bli_re.search(line)
         if bli_hit: 
@@ -934,7 +938,7 @@
         # freq table
         fqn_hit = fqn_re.search(line)
         if fqn_hit: 
-            fq_table = range(int(fqn_hit.group(1)))
+            fq_table = list(range(int(fqn_hit.group(1))))
             continue
         fqe_hit = fqe_re.search(line)
         if fqe_hit: 
@@ -1017,8 +1021,8 @@
     if verb:
         #print 'an',str(ant_names)
         #print 'ds',str(ds_indices)
-        print 'bl',str(bl_indices)
-        print 'fq',str(fq_table)
+        print('bl',str(bl_indices))
+        print('fq',str(fq_table))
     # and we want to reduce it to some usable one-liner
     reply = {}
     for prod in bl_indices:
@@ -1040,7 +1044,7 @@
     o.chanalia = []
     o.signature = set()
     o.chsig = {}
-    jl = map(lambda x:"%s_%s.input" % (o.job, x), sorted(o.rubbage.keys()))
+    jl = ["%s_%s.input" % (o.job, x) for x in sorted(o.rubbage.keys())]
     for job in jl:
         report = updateBLPOL(os.path.dirname(o.inputs) + '/' + job, o.verb)
         label = re.sub('.input','',job)
@@ -1067,7 +1071,7 @@
     Provide a report on the channels used by every baseline product
     '''
     for cha in o.chanalia:
-        print ' '.join(cha)
+        print(' '.join(cha))
 
 def doFFConf(o, detailed):
     '''
@@ -1080,15 +1084,15 @@
             for partner in sorted(list(o.chsig[sig])):
                 temp,peer = partner.split(':')
                 if temp != scan:
-                    print
+                    print()
                     scan = temp
                     #print sig,count,scan,
-                    print sig,' ',scan,
-                print peer,
+                    print(sig,' ',scan, end=' ')
+                print(peer, end=' ')
         else:
             #print sig,count,
-            print sig,' ',
-        print
+            print(sig,' ', end=' ')
+        print()
 
 # main entry point
 if __name__ == '__main__':
