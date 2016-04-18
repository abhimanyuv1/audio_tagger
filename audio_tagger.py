#!/usr/bin/python

import os
import argparse
from MediaInfoDLL import *	

MI = MediaInfo()

def find_file_format(root, file_name):
	print "Analysing file ...", file_name
	abs_file_path = root + file_name
	MI.Open(abs_file_path)
	print MI.Get(Stream.Audio, 0, u"Codec")
	print MI.Get(Stream.General, 0, u"CodecID")
	MI.Close()

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Audio auto tagger')
	parser.add_argument("-p", "--path", type=str, required=True, help="Audio folder path")

	args = parser.parse_args()

	print "Scanning ...", args.path
	for root, dirs, files in os.walk(args.path, topdown=False):
		for name in files:
			find_file_format(root, name)
