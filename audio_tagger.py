#!/usr/bin/python

import os
import argparse
import subprocess
import requests
import json
from MediaInfoDLL import *	

# https://acoustid.org/webservice
ACOUSTID_CLIENT_ID = "lkIelr9JXAQ"
ACOUSTID_API_SERVER = "http://api.acoustid.org/v2/lookup"

MI = MediaInfo()

def find_file_extension(root, file_name):
	print "Analysing file ...", file_name
	ext = ""
	abs_file_path = root + file_name
	MI.Open(abs_file_path)
	container = MI.Get(Stream.General, 0, u"CodecID")
	if not container:
		codec = MI.Get(Stream.Audio, 0, u"Codec")
		if codec == "MPA2L3":
			ext =".mp3"
	else:
		if container == "mp42":
			ext = ".m4a"
	MI.Close()
	return ext

def rename_file(oldroot, newroot, name, ext):
	filename, curr_ext = os.path.splitext(name)
	if curr_ext != ext:
		filename = filename + ext
		old_file_path = os.path.join(oldroot, name)
		new_file_path = os.path.join(newroot, filename)
		print "rename {} to {}".format(old_file_path, new_file_path)
		os.rename(old_file_path, new_file_path)

def get_fingerprint(root, name):
	FPCALC = "/usr/bin/fpcalc"
	output = subprocess.check_output([FPCALC, os.path.join(root, name)])
	output = output.split("\n")
	duration = output[1].split("=")[1]
	fingerprint = output[2].split("=")[1]
	return fingerprint, duration

def get_audio_info(fingerprint, duration):
	# Add server url
	url = ACOUSTID_API_SERVER
	# Add client
	url += "?client={}".format(ACOUSTID_CLIENT_ID)
	# Add meta
	url += "&meta=recordings+releasegroups+compress"
	# Add duration
	url += "&duration={}".format(duration)
	# Add fingerprint
	url += "&fingerprint={}".format(fingerprint)

	r = requests.get(url)
	print r.text

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Audio auto tagger')
	parser.add_argument("-p", "--path", type=str, required=True, help="Audio folder path")
	parser.add_argument("-o", "--output-path", type=str, required=False, help="Output folder path")

	args = parser.parse_args()

	print "Scanning ...", args.path
	output_path =  args.output_path
	if not output_path:
		output_path = args.path
	print "Output path ...", output_path

	if not os.path.exists(output_path):
		print "Creating output directory ...", output_path
		os.makedirs(output_path)

	for root, dirs, files in os.walk(args.path, topdown=False):
		for name in files:
			ext = find_file_extension(root, name)
			rename_file (root, output_path, name, ext)

	for root, dirs, files in os.walk(output_path, topdown=False):
		for name in files:
			print "Filename ", name
			fingerprint, duration = get_fingerprint(root, name)
			get_audio_info(fingerprint, duration)
