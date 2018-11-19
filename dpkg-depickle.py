#!/usr/bin/python
# 
# dpkg-depickle.py  
# compares Ubuntu package lists
#
###############################################################################
import sys
import re
import subprocess
import os
import os.path
import argparse
# possible arguments: none, file1. file1 and file2
parser = argparse.ArgumentParser(description="no arguments: diff the localhost package list (dpkg -l) with the latest manifest file")
parser.add_argument('file1', nargs='?', type=argparse.FileType('r'),  help="if you include one file diffs localhost with file1")
parser.add_argument('file2', nargs='?', type=argparse.FileType('r'),  help="include two files, diffs the file1 and file2")

args = parser.parse_args()

manifest_dir = "."
global newest_manifest 

if not os.geteuid() == 0:
    sys.exit('Script must be run as root')
	
########## defs ####################
# generic error function
def error(text):
	print "Error!"
	print "  " + text
	print " exiting..."
	sys.exit(-1)

# compare localhost against manifest if no file and against file if file
def compare(file):
	local = subprocess.Popen(['dpkg', '-l'], stdout=subprocess.PIPE)
	if not local:
		error("compare: Can't run dpkg -l correctly on local system!" )
		
	rfiledata = []
	lfiledata = []
	a = []
	b = []

	for line in local.stdout.readlines():
		lfiledata.append(line)
	a = process_data(lfiledata)
	
	# must be dpkg -l ...strip first 5 lines
	# save 2nd and third columns
	if file != "none":
		for line in file:
			rfiledata.append(line)
		file.close
	else:
		f = get_manifest_name()
		with open(manifest_dir + "/" + f, "r") as mfile:	
			for line in mfile:
				rfiledata.append(line)
		mfile.close	
	b = process_data(rfiledata)
				
	do_work(a, b)
		
def diff():
	rfiledata = []
	lfiledata = []
	a = []
	b = []
		#with open(l, "r") as lfile:
	# must be dpkg -l ...strip first 5 lines
	# save 2nd and third columns
	for line in args.file1:
		lfiledata.append(line)
	args.file1.close	
	a = process_data(lfiledata)

	for line in args.file2:
		rfiledata.append(line)
	args.file2.close	
	b = process_data(rfiledata)
			
	do_work(a, b)

	
def alphasort(ver, can):
	#sorts alphanum descending for dates like D140904
	# and versions like 4.5.6
	sortlist=[ver, can]
	sortlist.sort()
	if ver == can:
		return "equal"	# so we don't eval this case
	if sortlist[1] == ver:
		# returning the label so we can test at the other def
		# if we got ver back then we know to increment the newest manifest file name
		return "ver"
	else:
		return "can"

def get_manifest_name():
	#Gets the newest name ! in version-order ! from list of manifest files.
	global newest_manifest
	filelist = os.listdir(manifest_dir) 
	newest = ""
	candidate = [0, 0, 0, 0, 0]
	ver_list = []
	print "   ... Manifest directory " + manifest_dir + "\n"
	for i in filelist:
		# test for basic manifest pattern: <int>.<int>.<int>.[int]*-oa4*manifest
		# an optional fourth/fifth digit for nightly builds
		if not re.search('^\d+\.\d+\..*-oa4-.+\.manifest$', i):
			if re.search('\.manifest$', i ):
				print "    Ignoring:      " + i
			continue	
		# get lines as list of two parts, throw away second part
		line_list = re.split('-oa4', i)
		ver_list = re.split('\.', line_list[0]) 
		# get first part as list split on '.'
		# WARNING file name must be <int>.<int>.<int>[.int][.int]-oa4*.manifest
		# we had to use alphasort because we want 5.2.8.1 to be newer than 5.2.8.140904
		# which is a nightly of 5.2.8
		count = 0
		# The break statements are arranged so that as soon as we get a mismatch between 
		# ver and can, we break to the next filename
		for p in ver_list:
			t = alphasort(ver_list[count], candidate[count])
			if t == "ver":		# testing ver is newer than candidate
				candidate[count]  =  ver_list[count]
				newest = i
				count += 1
				break
			elif t == "can":	#can is newer than ver
				break
			count += 1
	#end of filelist loop		

	if candidate != [0, 0, 0, 0, 0]:
		print "\n## Using this manifest file: " + newest + " ##\n"
		newest_manifest = newest 	#for use in output
		return newest
	else:
		error("sort_manifests: could not find the latest manifest file, or could not sort the manifest list")


	
def process_data(filedata):
	c =[]			
	for line in filedata:
		#print "LINE:  " + line
		if re.match("Desired=Unknown", line) or re.match("\| Status=Not", line):
			# do nothing	
			n = "nothing"
		elif re.match('\|\/ Err\?=\(none\)\/', line) or re.match('\W+\sName\s+Version\s+.\w+', line) or re.match("\+\+\+-=====", line):
			# do nothing	
			n = "nada"
		elif re.match(r"(?P<status>\w+)(?P<name>[\w\S\sA-Za-z0-9_.-:+]+)(?P<version>[\w\S\sA-Za-z0-9_.-:+]+)\s+", line):
			# hack cough kluge warning
			crgx = re.match(r"(?P<status>\S+)\s+(?P<name>\S+)\s+(?P<version>\S+)\s+", line)
			if crgx:
				c.append(crgx.group('name') + "  " + crgx.group('version'))
		elif re.match(r"(?P<name>[\w\S\sA-Za-z0-9_.-:+]+) (?P<version>[\w\S\sA-Za-z0-9_.-:+]+)",line ):
			# simpler dpkg-query output get first and second word-like things separated by two spaces
			#print "matched dpkg QUERY"
			c.append(line.rstrip())
		else:
			error("Couldn't parse data: " + line)
	if not c:
		error(" process_data: list c is empty")
	else:
		return c

def do_work(a, b):
	if  not a:
		error("do_work: list a is empty")
	elif not b:
		error("do_work: list b is empty")		
	abdiff = []
	badiff  = []
	notlocal  = []
	notremote   = []
	diffversion  = []
	a1 = []; b1 = []
	# do first diffs comparing entire line	
	#inter = set(a).intersection(b)
	abdiff = set(a).difference(b)
	badiff = set(b).difference(a)

	if not abdiff and not badiff:
		if args.file2:
			print "\nThere is no difference between " + args.file1.name + " and "  + args.file2.name + ".\n"
		elif args.file1:
			print "\nThere is no difference between the local system and " + args.file1.name  + ".\n"
		else:
			print "\nThere is no difference between the local system and the manifest.\n"
		sys.exit(-1)	

	if abdiff and not badiff:   # case where local has all the packages of remote ( but not vice versa)
		badiff = set()
	elif badiff and not abdiff:	# where remote has all the packages of local ( but not vice versa)
		abdiff = set()
		
	sort_set(abdiff)
	sort_set(badiff)
	
	# make two arrays of names from compare results, splitting name and version on whitespace
	for line in badiff:
		bregx = re.match(r"(?P<name>[\w\S\sA-Za-z0-9_.-:+]+) (?P<version>[\w\S\sA-Za-z0-9_.-:+]+)",line ) 	
		if bregx:
			if bregx.group('name'):
				b1.append(bregx.group('name'))
			else:
				error("do_work: Can't parse this package in badiff- " + line)
			
	for line in abdiff:
		aregx = re.match(r"(?P<name>[\w\S\sA-Za-z0-9_.-:+]+) (?P<version>[\w\S\sA-Za-z0-9_.-:+]+)",line ) 
		if aregx:
			if aregx.group('name'):
				a1.append(aregx.group('name'))
			else:
				error("do_work:Can't parse this package in abdiff- " + line)
		
	if a1 and b1:
		notlocal = set(b1).difference(a1)
		notremote = set(a1).difference(b1)
		diffversion = set(a1).difference(notremote)
	elif a1 and not b1:
		notremote = set(a1).difference(b1)
		diffversion = set(a1).difference(notremote)
	elif b1 and not a1:
		notlocal = set(b1).difference(a1)
		diffversion = set(b1).difference(notlocal)
	else:
		error("do_work:a1 and/or b1 failed.")
	output(notlocal, notremote, diffversion, abdiff, badiff)
		
# careful! python sets are unsorted by definition so this has to be used 
# at the point of extraction of items in the set
def sort_set(myset): 
    """ Sort the given iterable in the way that humans expect.""" 
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(myset, key = alphanum_key)

# fixes non-backslashed plus (+) characters
# oddly, re accepts dots (..) and internally literalizes them but not pluses
# so "\+"  finds a + character and '\+'  adds a backslash to each
def patternfixer(pattern):
	new = re.sub("\+", '\+', pattern.rstrip())
	return new

def output(notlocal, notremote, diffversion, abdiff, badiff):
	global newest_manifest
	# deal with optional 2nd filename argument
	if args.file2:
		mysys = args.file1.name
		yoursys = args.file2.name
	elif args.file1:
		# no file2
		mysys = "LOCAL"
		yoursys = args.file1.name	
	else:
		mysys = "LOCAL"
		yoursys = newest_manifest
		
	# output from the comparisons ##################	
	print ""
	print "--------------------------------------------------------------------"	
	print "## Packages missing in " + mysys + " system, but listed in " + yoursys + " ##"
	if notlocal:
		for it in sort_set(notlocal):
			print "  " + it
	else:
		print "    none."
		
	print ""	
	print "--------------------------------------------------------------------"
	print "## Packages on " + mysys + " system, but missing in " + yoursys + " ##"
	if notremote:
		for it in sort_set(notremote):
			print "  " + it
	else:
		print "   none."
		
	print ""	
	print "--------------------------------------------------------------------"
	print "## Packages in with a different version  ##"
	print '{0:1} {1:40} {2:40} '.format("", mysys + " VERSION",  yoursys + " VERSION")				
	if diffversion:
		for diffitem in sort_set(diffversion):
			pattern = "^(?P<name>" + patternfixer(diffitem) + ") (?P<version>[\w\S\sA-Za-z0-9_.-:+]+)"
			for line in abdiff:
				dregx = re.match(pattern, line) 	
				if dregx:
					for remitem in badiff:
						cregx = re.match(pattern, remitem)
						if cregx:
							print '{0:1} {1:40} {2:40} '.format("", line, remitem)
	else:
		print "    none."
		
		
	print ""

	
########### execution begins here ############

# decide what to do based on args
if args.file1:
	if args.file2:
		#two file args - zdiff two files
		diff()
	else:
		#one file arg - compare local vs file
		compare(args.file1)
else:
	#no args at all compare local vs manifest
	compare("none")

	
sys.exit(-1)	
