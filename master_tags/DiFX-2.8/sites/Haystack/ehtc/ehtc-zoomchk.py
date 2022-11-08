--- ehtc-zoomchk.py	(original)
+++ ehtc-zoomchk.py	(refactored)
@@ -6,6 +6,8 @@
 ehtc-zoomchk.py -- a program to check zoom band uniformity across jobs
 '''
 
+from __future__ import absolute_import
+from __future__ import print_function
 import argparse
 import re
 
@@ -77,12 +79,12 @@
         zfir = str(zfirch)
         zfin = str(zfinch)
         antlist = '-'.join(
-            map(lambda x:x + ':' + str(antmap[x]),sorted(list(antmap))))
-        if o.verb: print '# Zoom %s..%s in %s %s' % (
-            zfir, zfin, jobin, antlist)
+            [x + ':' + str(antmap[x]) for x in sorted(list(antmap))])
+        if o.verb: print('# Zoom %s..%s in %s %s' % (
+            zfir, zfin, jobin, antlist))
         # still worth checking frequencies
         if len(cfrq) < 1:
-            raise Exception, 'Very odd, no zoom frequencies in ' + jobin
+            raise Exception('Very odd, no zoom frequencies in ' + jobin)
         cfrq.sort()
         mfqlst.add(cfrq[len(cfrq)/2])
         # for overall report
@@ -100,7 +102,7 @@
             jskip.append(jobin)
         antmap = {}
     if o.verb:
-        print '##\n## Zoom mid freq is ', ' '.join(sorted(mfqlst))
+        print('##\n## Zoom mid freq is ', ' '.join(sorted(mfqlst)))
         mfqlist = list(mfqlst)
         medianfreq = float(mfqlist[len(mfqlist)/2])
         if   medianfreq <  90000.0: medianband = '3 (GMVA)'
@@ -109,67 +111,67 @@
         elif medianfreq < 228100.0: medianband = 'b3 (Cycle4 6[USB]Lo)'
         elif medianfreq < 230100.0: medianband = 'b4 (Cycle4 6[USB]Hi)'
         else:                       medianband = '??? band 7 ???'
-        print '## Working with band %s based on median freq (%f)\n##' % (
-            medianband, medianfreq)
+        print('## Working with band %s based on median freq (%f)\n##' % (
+            medianband, medianfreq))
     if o.zmchk:
       # original logic
       if (len(zfirst) != 1 or len(zfinal) != 1 or
         len(jskip) > 0 or len(zoomys) > 1):
-        print '##'
-        print '## EITHER: Ambiguities in zoom freq ranges:'
-        print '##   first is %s, final is %s' % (str(zfirst), str(zfinal))
-        print '## OR: ALMA is not present in all jobs.'
-        print '##'
-        print '## You should review, and then execute this sequence:'
-        print '##'
+        print('##')
+        print('## EITHER: Ambiguities in zoom freq ranges:')
+        print('##   first is %s, final is %s' % (str(zfirst), str(zfinal)))
+        print('## OR: ALMA is not present in all jobs.')
+        print('##')
+        print('## You should review, and then execute this sequence:')
+        print('##')
         for j in jskip:
-            print '# skip %s since %s does not appear' % (j, o.alma)
-        print '#'
+            print('# skip %s since %s does not appear' % (j, o.alma))
+        print('#')
         for j in jlist:
-            print "jobs='%s'" % ' '.join(sorted(jlist[j]))
-            print "drivepolconvert.py -v $opts -l $pcal $jobs"
-            print '#'
-        print '## Be sure to reset the variable jobs to the original list'
-        print '## for subsequent processing, e.g.'
-        print '#'
-        print 'eval `$ehtc/ehtc-joblist.py -i $dout/$evs -o *.obs $jselect -J`'
-        print '#'
+            print("jobs='%s'" % ' '.join(sorted(jlist[j])))
+            print("drivepolconvert.py -v $opts -l $pcal $jobs")
+            print('#')
+        print('## Be sure to reset the variable jobs to the original list')
+        print('## for subsequent processing, e.g.')
+        print('#')
+        print('eval `$ehtc/ehtc-joblist.py -i $dout/$evs -o *.obs $jselect -J`')
+        print('#')
       else:
         o.zfirst = int(zfirst.pop())
         o.zfinal = int(zfinal.pop())
-        if o.verb: print 'Zoom frequency indices %d..%d found in %s..%s' % (
-            o.zfirst, o.zfinal, o.nargs[0], o.nargs[-1])
-        print '## All jobs are compatible with the same zoom range:',
-        for z in zoomys: print '##', z
+        if o.verb: print('Zoom frequency indices %d..%d found in %s..%s' % (
+            o.zfirst, o.zfinal, o.nargs[0], o.nargs[-1]))
+        print('## All jobs are compatible with the same zoom range:', end=' ')
+        for z in zoomys: print('##', z)
     elif len(jskip) > 0:
         # alma missing from some scans
-        print '##'
-        print '## Warning, ALMA is missing from some scans:'
-        print '## be certain you do not polconvert them'
-        print '##'
+        print('##')
+        print('## Warning, ALMA is missing from some scans:')
+        print('## be certain you do not polconvert them')
+        print('##')
         for j in jskip:
-            print '# skip %s since %s does not appear' % (j, o.alma)
-        print '#'
+            print('# skip %s since %s does not appear' % (j, o.alma))
+        print('#')
         jok = []
         for j in jlist:
             jok = jok + jlist[j]
-        print "jobs='%s'" % ' '.join(sorted(jok))
-        print "drivepolconvert.py -v $opts -l $pcal $jobs"
-        print '#'
-        print '# But be certain to reset $jobs to the full set after'
-        print '# you finish the PolConvert step so that these scans'
-        print '# are included in the tarballs.'
-        print '#'
+        print("jobs='%s'" % ' '.join(sorted(jok)))
+        print("drivepolconvert.py -v $opts -l $pcal $jobs")
+        print('#')
+        print('# But be certain to reset $jobs to the full set after')
+        print('# you finish the PolConvert step so that these scans')
+        print('# are included in the tarballs.')
+        print('#')
     else:
         # all are the same and alma present
         o.zfirst = int(sorted(list(zfirst))[0])
         o.zfinal = int(sorted(list(zfinal))[-1])
-        if o.verb: print '## Zoom frequency indices %d..%d in %s\n##  ..%s' % (
-            o.zfirst, o.zfinal, o.nargs[0], o.nargs[-1])
-        print '## We believe PolConvert can handle these:',
-        print '##',
-        for z in zoomys: print z,
-        print
+        if o.verb: print('## Zoom frequency indices %d..%d in %s\n##  ..%s' % (
+            o.zfirst, o.zfinal, o.nargs[0], o.nargs[-1]))
+        print('## We believe PolConvert can handle these:', end=' ')
+        print('##', end=' ')
+        for z in zoomys: print(z, end=' ')
+        print()
 
 #
 # enter here to do the work
