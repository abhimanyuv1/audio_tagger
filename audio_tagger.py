#!/usr/bin/python

import os
import argparse
import subprocess
import requests
import json
import taglib
from pymediainfo import MediaInfo

# https://acoustid.org/webservice
ACOUSTID_CLIENT_ID = "g4mgdCmxmd"  # registered id
ACOUSTID_API_SERVER = "http://api.acoustid.org/v2/lookup"

def find_file_extension(root, file_name):
    ext = ""
    codec = ""
    container = ""
    abs_file_path = os.path.join(root, file_name)
    print "Analysing file ...", abs_file_path
    media_info = MediaInfo.parse(abs_file_path)
    for track in media_info.tracks:
        if track.track_type == 'General':
            container = track.codec_id
        if track.track_type == 'Audio':
            codec = track.codec

    if container is not None:
        container = container.strip()

    if codec is not None:
        codec = codec.strip()

    if container is None:
        if codec in ["MPA2L3", "MPA1L3"]:
            ext = ".mp3"
    elif container == 'M4A':
            ext = ".m4a"

    print "container: {}, codec: {}, ext: {}".format(container, codec, ext)
    return ext


def rename_and_append_ext(oldroot, newroot, name, ext):
    filename, curr_ext = os.path.splitext(name)
    if curr_ext != ext:
        filename = filename + ext
        old_file_path = os.path.join(oldroot, name)
        new_file_path = os.path.join(newroot, filename)
        print "rename {} to {}".format(old_file_path, new_file_path)
        os.rename(old_file_path, new_file_path)


def rename_filename(oldroot, newroot, oldname, newname):
    if not newname:
        print "Empty new name, cant rename!"
        return

    _, old_ext = os.path.splitext(oldname)

    newname = newname + old_ext
    old_file_path = os.path.join(oldroot, oldname)
    new_file_path = os.path.join(newroot, newname)
    print "rename {} to {}".format(old_file_path, new_file_path)
    os.rename(old_file_path, new_file_path)


def get_fingerprint(root, name):
    FPCALC = "./fpcalc_bin/fpcalc"
    output = subprocess.check_output([FPCALC, os.path.join(root, name)])
    output = output.split("\n")
    duration = output[1].split("=")[1]
    fingerprint = output[2].split("=")[1]
    return fingerprint, duration


def get_audio_meta(name, fingerprint, duration):
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

    print "Querying for metadata...", name
    r = requests.get(url)
    return r.text


def parse_audio_json_data(audio_json_data):
    title = ""
    artist = ""
    #print "Json raw data", audio_json_data
    data = json.loads(audio_json_data)
    if data["status"] == "ok":
        try:
            # Only interested in first entry as that is with highest matching score
            title = data["results"][0]["recordings"][0]["title"]
            artist = data["results"][0]["recordings"][0]["artists"][0]["name"]
        except (KeyError, IndexError):
            print "Track metadata is not found in acoustid database, json_output: ", audio_json_data
    else:
        print "Status is NOK, json output: ", audio_json_data
    return title.encode('utf-8'), artist.encode('utf-8')


def add_tags_to_audio(root, name, title, artist):
    f = taglib.File(os.path.join(root, name))
    f.tags[u"ARTIST"] = [artist]
    f.tags[u"TITLE"] = [title]
    f.save()
    print f.tags


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Audio auto tagger')
    parser.add_argument("-p", "--path", type=str, required=True, help="Audio folder path")
    parser.add_argument("-o", "--output-path", type=str, required=False, help="Output folder path")

    args = parser.parse_args()

    in_path = os.path.abspath(os.path.expanduser(args.path))
    print "Scanning ...", in_path
    if args.output_path:
        output_path = os.path.abspath(os.path.expanduser(args.output_path))
    else:
        output_path = in_path
    print "Output path ...", output_path

    if not os.path.exists(output_path):
        print "Creating output directory ...", output_path
        os.makedirs(output_path)

    for root, dirs, files in os.walk(in_path, topdown=False):
        for name in files:
            ext = find_file_extension(root, name)
            rename_and_append_ext(root, output_path, name, ext)

    for root, dirs, files in os.walk(output_path, topdown=False):
        for name in files:
            fingerprint, duration = get_fingerprint(root, name)
            audio_json_data = get_audio_meta(name, fingerprint, duration)
            title, artist = parse_audio_json_data(audio_json_data)
            print "Title={}, Artist={}".format(title, artist)
            add_tags_to_audio(root, name, title, artist)
            rename_filename(root, output_path, name, title)
