#!/usr/bin/python
#
# Reads a raw Mark5B file and splits it into multiple files
# according to gaps in the timestamps.
#
# (C) 2021 Jan Wagner
#

import sys
import struct
import collections
import getopt

def usage():
	print ('m5bcontinuitycheck.py [-v] [-b|--bigendian] [-p|--progress] [--framesize=<n bytes>] <filename>')
	print ('  --v           : prints every frame')
	print ('  --bigendian   : specify when data are VDIF-like but with wrong Endianness')
	print ('  --progress    : show a progress bar per thread')
	print ('  --framesize=n : override the frame size otherwise taken from VDIF headers')
	sys.exit(-1)

def m5b_decode_header(data,fmt):
	s = struct.unpack(fmt,data)
	h = {}

	# Mark5B
	h['sync'] = (s[0] == 0xABADDEED)
	h['fillpattern'] = (s[0] == 0x11223344) or (s[1] == 0x11223344) or (s[2] == 0x11223344)
	h['size'] = 10016
	if h['sync']:
		dayStr = str(hex(s[2]))
		try:
			h['sec'] = int(dayStr[2:5])*86400 + int(dayStr[5:10])
			h['frame'] = s[1] & 0x7FFF  # bit15:TVG_ENA, bit[14:0]:frameNr
		except:
			h['sync'] = False
	else:
		h['sec'] = -1
		h['frame'] = 0
	return h

fmt_littleendian = '<IIII'  # 4 words, 32 bits
fmt_bigendian = '>IIII'

verbose = False         # default: don't print every frame
progressbar = False     # default: don't show a per-thread progress bar
fmt = fmt_littleendian  # default: VDIF is little endian, "other" formats are big endian
fmt_is_little = True
user_framesize = 0      # default: use frame size in the headers, do not override

split_gap_seconds = 10  # default: split input file at positions where timestamp jump by >=10 sec

try:
	optlist, args = getopt.getopt(sys.argv[1:], "vbps:", ["verbose","bigendian","framesize="])
except getopt.GetoptError:
	usage()

for opt, optarg in optlist:
	if opt == '-b' or opt == '--bigendian':
		fmt = fmt_bigendian
		fmt_is_little = False
	elif opt == '-s' or opt == '--framesize':
		user_framesize = int(optarg)
	elif opt == '-p' or opt == '--progress':
		progressbar = True
	elif opt == '-v' or opt == '--verbose':
		verbose = True
	else:
		usage()

if (len(args) != 1):
	usage()

frame_len = 10016
header_len = struct.calcsize(fmt)
filename = args[0]

f = open(filename, "rb")

th_sec = -1
th_frames = []
th_invalid_frames = []
th_byteoffsets = []
peak_fps = 1
nfill = 0
ngarbagebytes = 0
skipsize = 4  # initially, length of fill 0x11223344

outfile = None
outfilename = 'n/a'

done = False
while not(done):

	streampos = f.tell()
	header = f.read(header_len)
	if not header:
		done = True
		print ('EOF')
		break

	h = m5b_decode_header(header,fmt)
	if verbose:
		print ('%s %d \r' % (str(h),f.tell())),

	if h['fillpattern']:
		if skipsize > 0:
			tmp = f.read(skipsize)
		nfill += 1
		continue

	if not h['sync']:
		olost = f.tell()
		while not h['sync']:
			header = f.read(header_len)
			h = m5b_decode_header(header,fmt)
			if not header:
				done = True
				print ('EOF')
				break
		if done:
			break
		ofound = f.tell()
		ngarbagebytes += (ofound-olost)
		# print('Regained sync after %d bytes' % (ofound-olost))

	skipsize = h['size'] - header_len
	if (user_framesize > 0):
		skipsize = user_framesize - header_len
	#f.seek(skipsize, 1)  # fails at 2GB boundary!?
	payload = f.read(skipsize)

	# Skip invalid frames (sometimes timestamp is not correct... in Mark6 rec software...)
	if not h['sync']:
		th_invalid_frames.append(h['frame'])
		continue

	# Frames per sec
	if h['frame'] >= peak_fps:
		peak_fps = h['frame'] + 1

	# Summaries at each integer-second change or at EOF:
	if th_sec == -1:
		th_sec = h['sec']
		outfilename = './split/sec_%d.m5a' % (h['sec'])
		outfile = open(outfilename, 'w')

	if (abs(th_sec - h['sec']) >= split_gap_seconds):
		outfile.close()
		outfilename = './split/sec_%d.m5a' % (h['sec'])
		outfile = open(outfilename, 'w')
		dt = abs(th_sec - h['sec'])
		print('Time gap of %d seconds exceeds %d-second limit. Starting new file %s' % (dt,split_gap_seconds,outfilename))

	if (th_sec != h['sec']) or done:
		if len(th_frames) <= 0:
			# no valid frames at all
			nrange = 0
			nrmissing = -1
			nrdup = 0
			nrOO = -1
		else:
			nrange = max(th_frames) - min(th_frames) + 1
			uniques = len(th_frames) # DUMMY
			nrmissing = peak_fps - uniques
			nrdup = len(th_frames) - uniques
			nrOO = 0
			fn_prev = th_frames[0]
			fn_peak = th_frames[0]

		# Current thread reporting
		if verbose:
			sys.stdout.write("\033[K")
		print ('Second %-6d : %6d frames : #%d--#%d : %d lost, %d out-of-order, %d invalid, %d dup, of %d total : into %s' %
			( th_sec, len(th_frames), min(th_frames),
			  max(th_frames), nrmissing, nrOO, len(th_invalid_frames), nrdup, nrange, outfilename
			) 
		)
		if nfill > 0 or ngarbagebytes > 0:
			print ('Garbage data : %d fill pattern frames, %d garbage bytes between frames' % (nfill,ngarbagebytes))

		# Restart frame storage
		th_sec = h['sec']
		th_frames = []
		th_invalid_frames = []
		th_byteoffsets = streampos
		nfill = 0
		ngarbagebytes = 0

	th_frames.append(h['frame'])

	outfile.write(header)
	outfile.write(payload)

	# Visualize the frame count in current thread?
	if progressbar:
		N = len(th_frames)
		Nmax = 80
		if N < Nmax:
			print (tID, str(th_frames[0]) + '.'*(len(th_frames)-1) )
		else:
			print (tID, str(th_frames[0]) + '.'*(Nmax-2) + '<' + str(N-Nmax+1) + ' more>')
