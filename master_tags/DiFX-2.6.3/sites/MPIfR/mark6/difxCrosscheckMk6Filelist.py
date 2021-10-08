#!/usr/bin/python3
'''
Usage: difxCrosscheckMk6Filelist.py <command> <command args>

Available commands and their arguments:

   filelist <station.filelist> 

      Compares the content of file list against a Mark6 host.

      The content of the filelist must follow a pattern of
        /mark6-<nr>_fuse/<path>/<name>.vdif <mjd> <mjd>
      where mark6-<nr> is also the hostname of the Mark6 unit.

   msn <8-letter MSN> <Mark6 host> 

      Compares the content of DiFX dirlist against a Mark6 host.

      A directory list for the MSN must exist under $MARK5_DIR_PATH.
      The content of that MSN-associated directory list must follow
         <scanname>.vdif <mjd> <mjd> [<bytes>]

Reports any inconsistency between scans found in the list and scans
actually present on the loaded and mounted Mark6 module(s). It is
not necessary to FUSE-mount the modules.
'''


from typing import List, Dict, Tuple
import os, sys, subprocess


def get_filelist_content(filename: str, remotehost: str = '') -> List[Tuple[str,str,str]]:
	'''Collects Mark6 scan names and where possible also host names (default:blank) from a DiFX file list'''	
	scans = []
	scannames = set()
	hostnames = set()
	with open(filename, 'r') as f:
		for line in f:
			line = line.strip()
			if len(line) < 1 or line[0] == '#':
				continue

			# Parse 'line' expected in two formats:
			#   /mark6-<nr>_fuse/<path>/<name>.vdif <mjd> <mjd>
			#   <scanname>.vdif <mjd> <mjd>

			scanpath = line.split()[0]
			pathcomponents = scanpath.split('/')
			scanname = pathcomponents[-1]
			hostname = remotehost

			if len(pathcomponents) > 1:
				mountpoint = pathcomponents[1]  # e.g. mark6-03_fuse
				if len(mountpoint.split('_')) is not 2:
					print ("Warning: filelist %s scan %s mountpoint %s doesn't look like 'mark6-<nr>_fuse'. Skipping." % (scanpath, scanname, mountpoint))
					continue
				hostname = mountpoint.split('_')[0]

			if scanname in scannames:
				print ("Warning: filelist %s has duplicate scan %s" % (scanpath, scanname))
				continue

			scannames.add(scanname)
			hostnames.add(hostname)
			scans.append((hostname,scanname,scanpath))

	if len(hostnames)>1:
		print ("Error: filelist refers to %d different Mark6 units, currently not supported." % (len(hostnames)))
		sys.exit(1)

	return scans



def get_mark6_scanlist(hostname: str, msn: str = '') -> List[str]:
	'''Connects via SSH to the Mark6 and looks up *all* files under the standard mountpoints'''
	scans = []

	if len(msn) < 1:
		# pattern = '/%s_fuse/*/' % (hostname.strip())
		pattern = '/mnt/disks/?/?/'
		cmd = ["/usr/bin/ssh", hostname, "/usr/bin/find", pattern, "-name", '"*.vdif"']
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(st,rc) = p.communicate()
		if len(rc) > 1:
			print('Probable error message during SSH to host: %s' % (str(rc)))
		filenames = [str(filename).strip() for filename in st.split()]
		scannames = [filename.split('/')[-1] for filename in filenames]
		scans = list(set(scannames))
	else:
		# TODO: need to look at .meta directories to decide on MSN
		pass

	return scans


def check_filelist(filename: str) -> bool:

	userlist = get_filelist_content(filename)
	if len(userlist) < 1:
		return True
	hostname = userlist[0][0]  # currently only one host for all scans is supported...
	modulelist = get_mark6_scanlist(hostname)
	# ... compare
	return True


def check_dirlist(MSN: str, remotehost: str) -> bool:

	dirlistfile = os.environ['MARK5_DIR_PATH'] + "/" + MSN + ".filelist"
	userlist = get_filelist_content(dirlistfile, remotehost)
	userscans = [item[1] for item in userlist]  # extract just the pathless file name from (host,file,path+file) tuple
	userscans = set(userscans)

	modulelist = get_mark6_scanlist(args[1], msn='')

	print('Dirlist has %d entries, module has %d scans' % (len(userscans), len(modulelist)))
	print(userscans)
	print(modulelist)

	return True


if __name__ == "__main__":

	argsOk = True
	comparisonOk = True

	if '--help' in sys.argv or '-h' in sys.argv or len(sys.argv) not in [3,4]:
		argsOk = False

	else:
		cmd = sys.argv[1]
		args = sys.argv[2:]

		if cmd == 'filelist':
			comparisonOk = check_filelist(filename=args[0])
		elif cmd == 'msn':
			comparisonOk = check_dirlist(MSN=args[0], remotehost=args[1])
		else:
			argsOk = False

	if not argsOk:
		print(__doc__)
		sys.exit(0)
