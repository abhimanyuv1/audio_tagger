#!/usr/bin/python

import os
import argparse
import subprocess
import requests
import json
from MediaInfoDLL import MediaInfo, Stream

# https://acoustid.org/webservice
ACOUSTID_CLIENT_ID = "g4mgdCmxmd"	# registered id
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

def get_audio_meta(fingerprint, duration):
	# Add server url
	url = ACOUSTID_API_SERVER
	# Add client
	url += "?client={}".format(ACOUSTID_CLIENT_ID)
	# Add meta
	url += "&meta=recordings+compress"
	# Add duration
	url += "&duration={}".format(duration)
	# Add fingerprint
	url += "&fingerprint={}".format(fingerprint)

	print "Querying for metadata..."
	r = requests.get(url)
	return r.text

def parse_audio_json_data(audio_json_data):
	title = ""
	artist = ""
	print "Json raw data", audio_json_data
	data = json.loads(audio_json_data)
	if data["status"] == "ok":
		# Only interested in first entry as that is with highest matching score
		title = data["results"][0]["recordings"][0]["title"]
		artist = data["results"][0]["recordings"][0]["artists"][0]["name"]
	else:
		print "Status is NOK"

	return title, artist

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Audio auto tagger')
	parser.add_argument("-p", "--path", type=str, required=True, help="Audio folder path")
	parser.add_argument("-o", "--output-path", type=str, required=False, help="Output folder path")

	args = parser.parse_args()

	in_path = os.path.abspath(os.path.expanduser(args.path))
	print "Scanning ...", in_path
	if args.output_path:
		output_path =  os.path.abspath(os.path.expanduser(args.output_path))
	else:
		output_path = in_path
	print "Output path ...", output_path

	if not os.path.exists(output_path):
		print "Creating output directory ...", output_path
		os.makedirs(output_path)

	for root, dirs, files in os.walk(in_path, topdown=False):
		for name in files:
			ext = find_file_extension(root, name)
			rename_file (root, output_path, name, ext)

	for root, dirs, files in os.walk(output_path, topdown=False):
		for name in files:
			print "Filename ", name
			fingerprint, duration = get_fingerprint(root, name)
			audio_json_data = get_audio_meta(fingerprint, duration)
			title, artist = parse_audio_json_data(audio_json_data)
			print "Title={}, Artist={}".format(title, artist)
