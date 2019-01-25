#!/usr/bin/env python3

import os
import sys
import subprocess

from . import form
from . import consts
from . import youtube as yt

import pyforms_lite


def main():
    if "linux" in sys.platform:  # root needed for writing files
        if os.geteuid() != 0:
            print("Need sudo for writing files")
            subprocess.call(['sudo', 'python3', sys.argv[0]])
    # Always get the initial YT credentials outside of a thread. Threads break the setup process.
    try:
        consts.yt = yt.get_youtube_service()
        pyforms_lite.start_app(form.MeleeUploader, geometry=(200, 200, 1, 1))
    except Exception as e:
        print("This program needs internet access to work")
        sys.exit(1)


def ult():
    consts.melee = False
    main()


if __name__ == "__main__":
    main()
