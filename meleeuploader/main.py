#!/usr/bin/env python3

import os
import sys

from . import forms
from . import consts
from . import youtube as yt

import pyforms_lite


def main():
    try:
        consts.youtube = yt.get_youtube_service()
    except Exception as e:
        print(e)
        print("There was an issue with getting Google Credentials")
        sys.exit(1)
    try:
        consts.sheets = yt.get_spreadsheet_service()
    except Exception as e:
        pass
    try:
        pyforms_lite.start_app(forms.MeleeUploader, geometry=(200, 200, 1, 1))
    except Exception as e:
        print("Error:", e)
        sys.exit(1)


def ult():
    consts.melee = False
    main()


if __name__ == "__main__":
    main()
