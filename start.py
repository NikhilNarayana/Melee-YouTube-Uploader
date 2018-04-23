#!/usr/bin/env python3

import os
import csv
import sys
import errno
import socket
import threading
from time import sleep
from decimal import Decimal

from youtubeAuthenticate import *

from PyQt5 import QtCore, QtGui
import pyforms
from argparse import Namespace
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlFile
from pyforms.controls import ControlTextArea, ControlList
from pyforms.controls import ControlCombo, ControlProgress
from pyforms.controls import ControlButton, ControlCheckBox


class EmittingStream(QtCore.QObject):

    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass


class Melee_Uploader(BaseWidget):

    def __init__(self):
        super(Melee_Uploader, self).__init__("Melee YouTube Uploader")
        # Redirct print output
        sys.stdout = EmittingStream(textWritten=self.writePrint)
        # get YouTube
        self._youtube = get_youtube_service()
        # Create form fields
        # Event Values
        self._where = ControlCombo("File Location")
        self._ename = ControlText("Event Name")
        self._pID = ControlText("Playlist ID")
        self._bracket = ControlText("Bracket Link")
        # Match Values
        self._file = ControlFile("File")
        self._p1 = ControlText("Player 1")
        self._p2 = ControlText("Player 2")
        self._p1char = ControlCombo("P1 Character")
        self._p2char = ControlCombo("P2 Character")
        self._mtype = ControlCombo("Match Type")
        self._i = 0

        # Output Box
        self._output = ControlTextArea()
        self._output.readonly = True

        # Button
        self._button = ControlButton('Submit')

        # Form Layout
        self.formset = [{"-Match": ["_file", (' ', "_mtype", ' '), (' ', "_p1", ' '), (' ', "_p1char", ' '), (' ', "_p2", ' '), (' ', "_p2char", ' ')],
                         "-Status-": ["_output"],
                         "Event-": [(' ', "_where", ' '), (' ', "_ename", ' '), (' ', "_pID", ' '), (' ', "_bracket", ' ')]},
                        (' ', '_button', ' ')]

        # Set TBA check

        # Add ControlCombo values
        self._where += ("Parent Folder", "../")
        self._where += ("Same Folder", "")
        self._mtype += "Pools"
        self._mtype += "Winners"
        self._mtype += "Losers"
        self._mtype += "Winners Finals"
        self._mtype += "Losers Finals"
        self._mtype += "Grand Finals"
        self._mtype += "Money Match"
        self._mtype += "Crew Battle"
        chars = ['Fox', 'Falco', 'Marth', 'Sheik', 'Jigglypuff', 'Peach', 'Captain Falcon', 'Ice Climbers', 'Pikachu', 'Samus', 'Dr. Mario', 'Yoshi', 'Luigi', 'Ganondorf', 'Mario', 'Young Link', 'Donkey Kong', 'Link', 'Mr. Game & Watch', 'Mewtwo', 'Roy', 'Zelda', 'Ness', 'Pichu', 'Bowser', 'Kirby']
        for char in chars:
            self._p1char += char
            self._p2char += char

        # Define the button action
        self._button.value = self.__buttonAction

        # Get latest values from form_values.csv
        try:
            with open('form_values.csv') as csvfile:
                reader = csv.reader(csvfile, delimiter=',', quotechar='|')
                i = 0
                for row in reader:
                    for val in row:
                        if val is not "":
                            switcher = {
                                0: self._where,
                                1: self._ename,
                                2: self._pID,
                                3: self._mtype,
                                4: self._p1,
                                5: self._p2,
                                6: self._p1char,
                                7: self._p2char,
                                8: self._bracket
                            }
                            switcher[i].value = val
                        i = i + 1
                    break
        except (IOError, OSError, StopIteration) as e:
            print("No form_values.csv to read from, continuing with default values and creating file")
            with open("form_values.csv", "w+") as csvf:  # if the file doesn't exist
                csvf.write(''.join(str(x) for x in [","] * 8))

    def __buttonAction(self):
        """Button action event"""
        reader = None
        try:
            reader = csv.reader(open('form_values.csv'))
        except (StopIteration, IOError, OSError) as e:
            with open("form_values.csv", "w+") as csvf:  # if the file doesn't exist
                csvf.write(''.join(str(x) for x in [","] * 8))
            reader = csv.reader(open("form_values.csv"))
        row = next(reader)
        row[0] = self._where.value
        row[1] = self._ename.value
        f = self._pID.value.find("PL")
        self._pID.value = self._pID.value[f:f + 34]
        row[2] = self._pID.value
        row[3] = self._mtype.value
        row[4] = self._p1.value
        row[5] = self._p2.value
        row[6] = self._p1char.value
        row[7] = self._p2char.value
        row[8] = self._bracket.value
        thr = threading.Thread(target=self._init)
        thr.daemon = True
        thr.start()
        writer = csv.writer(open('form_values.csv', 'w'))
        writer.writerow(row)

    def _init(self):
        title = "{ename} - {mtype} - ({p1char}) {p1} vs {p2} ({p2char})".format(mtype=self._mtype.value, ename=self._ename.value, p1=self._p1.value, p2=self._p2.value, p1char=self._p1char.value, p2char=self._p2char.value)
        # for f in self._files:
        #     fl = f.lower()
        #     if all(k in fl for k in (self._p1.value.lower(), self._p2.value.lower(), self._mtype.value.lower())):
        #         self._file = f
        #         break
        credit = "Uploaded with Melee-Youtube-Uploader (https://github.com/NikhilNarayana/Melee-YouTube-Uploader) by Nikhil Narayana"
        descrip = ("""Bracket: {}\n\n""".format(self._bracket.value) + credit) if self._bracket.value else credit
        tags = ["Melee", "Super Smash Brothers Melee", "Smash Brother", "Super Smash Bros. Melee"]
        tags.append(self._p1char.value)
        tags.append(self._p2char.value)
        tags.append(self._ename.value)
        tags.append(self._p1.value)
        tags.append(self._p2.value)
        body = dict(
            snippet=dict(
                title=title,
                description=descrip,
                tags=tags,
                categoryID=20
            ),
            status=dict(
                privacyStatus="public")
        )
        insert_request = self._youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=MediaFileUpload(self._file.value,
                                       chunksize=10485760,
                                       resumable=True),)
        vid = self._upload(insert_request)
        self._youtube.playlistItems().insert(
            part="snippet",
            body=dict(
                snippet=dict(
                    playlistId=self._pID.value,
                    resourceId=dict(
                        kind='youtube#video',
                        videoId=vid)))).execute()
        print("Added to playlist")
        print("DONE\n")

    def _upload(self, insert_request):
        retry_exceptions = get_retry_exceptions()
        retry_status_codes = get_retry_status_codes()
        ACCEPTABLE_ERRNO = (errno.EPIPE, errno.EINVAL, errno.ECONNRESET)
        try:
            ACCEPTABLE_ERRNO += (errno.WSAECONNABORTED,)
        except AttributeError:
            pass  # Not windows
        print("Uploading {}".format(self._file.value))
        while True:
            try:
                status, response = insert_request.next_chunk()
                if status is not None:
                    percent = Decimal(int(status.resumable_progress) / int(status.total_size))
                    print("{}% uploaded".format(round(100 * percent, 2)))
            except HttpError as e:
                if e.resp.status in retry_status_codes:
                    print("A retriable HTTP error {} occurred:\n{}".format(e.resp.status, e.content))
            except retry_exceptions as e:
                print("A retriable error occurred: {}".format(e))

            except Exception as e:
                if e in ACCEPTABLE_ERRNO:
                    print("Retriable Error occured, retrying now")
                else:
                    print(e)
                pass
            if response:
                if "id" in response:
                    print("Video link is https://www.youtube.com/watch?v={}".format(response['id']))
                    return response['id']
                else:
                    print(response)
                    print(status)
                    exit("Upload failed, no id in response")

    def writePrint(self, text):
        self._output.value += text
        self._output._form.plainTextEdit.moveCursor(QtGui.QTextCursor.End)
        print(text, file=sys.__stdout__, end='')


def internet(host="www.google.com", port=80, timeout=4):
    try:
        host = socket.gethostbyname(host)
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except Exception as e:
        print(e)
        print("No internet!")
        return False


def main():
    if "linux" in sys.platform:  # root needed for writing files
        if os.geteuid() != 0:
            print("Need sudo for writing files")
            subprocess.call(['sudo', 'python3', sys.argv[0]])
    get_youtube_service()
    if internet():
        pyforms.start_app(Melee_Uploader, geometry=(100, 100, 1, 1))  # 1, 1 shrinks it to the smallest possible size
    else:
        return


if __name__ == "__main__":
    main()
