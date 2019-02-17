#!/usr/bin/env python3

import os
import sys
import json
import subprocess
import pkg_resources

from . import forms
from . import consts
from . import youtube as yt

import requests
import pyforms_lite

__version__ = pkg_resources.require("MeleeUploader")[0].version


def main():
    try:
        json_information = requests.get('https://pypi.python.org/pypi/meleeuploader/json').text
        latest_version = json.loads(json_information)['info']['version']
        if (__version__ != latest_version):
            resp = input(f"Version {latest_version} is available, would you like to update? (y/n) ")
            if any(x == resp for x in ("y", "yes", "Yes")):
                subprocess.call(('pip3', 'install', '-U', 'meleeuploader'))
                print("You can now restart the app to use the new version")
    except Exception as e:
        print("Error: " + e)
    try:
        consts.youtube = yt.get_youtube_service()
        consts.sheets = yt.get_spreadsheet_service()
    except Exception as e:
        print(e)
        print("There was an issue with getting Google Credentials")
        sys.exit(1)
    try:
        pyforms_lite.start_app(forms.MeleeUploader, geometry=(200, 200, 1, 1))
    except Exception as e:
        print("Error:" + e)
        sys.exit(1)


def ult():
    consts.melee = False
    main()


if __name__ == "__main__":
    main()
