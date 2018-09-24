#!/usr/bin/env python3

import os
import sys
import json
import errno
import socket
import threading
from time import sleep
from queue import Queue
from copy import deepcopy
from decimal import Decimal

from .viewer import *
from .youtubeAuthenticate import *

import pyforms_lite
from argparse import Namespace
from PyQt5 import QtCore, QtGui
from pyforms_lite import BaseWidget
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from pyforms_lite.controls import ControlText, ControlFile
from pyforms_lite.controls import ControlTextArea, ControlList
from pyforms_lite.controls import ControlCombo, ControlProgress
from pyforms_lite.controls import ControlButton, ControlCheckBox, ControlCheckBoxList

class EmittingStream(QtCore.QObject):

    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass


class MeleeUploader(BaseWidget):

    def __init__(self):
        super(MeleeUploader, self).__init__("Melee YouTube Uploader")
        # Redirct print output
        sys.stdout = EmittingStream(textWritten=self.writePrint)

        # Queue
        self._queue = Queue()
        self._queueref = []
        self._firstrun = True

        # get YouTube
        self._youtube = get_youtube_service()
        # Create form fields
        # Event Values
        self._ename = ControlText("Event Name")
        self._pID = ControlText("Playlist ID")
        self._bracket = ControlText("Bracket Link")
        # Match Values
        self._file = ControlFile("File")
        self._p1 = ControlText("Player 1")
        self._p2 = ControlText("Player 2")
        self._p1char = ControlCheckBoxList("P1 Characters")
        self._p2char = ControlCheckBoxList("P2 Characters")
        self._mtype = ControlCombo("Match Type")

        # Output Box
        self._output = ControlTextArea()
        self._output.readonly = True
        self._qview = ControlList("Queue", select_entire_row=True)
        self._qview.cell_double_clicked_event = self.__show_o_view
        self._qview.readonly = True
        self._qview.horizontal_headers = ["Player 1", "Player 2", "Match Type"]

        # Button
        self._button = ControlButton('Submit')

        # Form Layout
        self.formset = [{"-Match": ["_file", (' ', "_mtype", ' '), (' ', "_p1", ' '), (' ', "_p1char", ' '), (' ', "_p2", ' '), (' ', "_p2char", ' ')],
                         "-Status-": ["_output", "=", "_qview"],
                         "Event-": [(' ', "_ename", ' '), (' ', "_pID", ' '), (' ', "_bracket", ' ')]},
                        (' ', '_button', ' ')]

        # Main Menu Layout
        self.mainmenu = [{
            'Settings': [{
                'Remove Youtube Credentials': self.__reset_cred_event
                }]
        }]

        # Add ControlCombo values
        self._mtype += "Pools"
        self._mtype += "Winners"
        self._mtype += "Losers"
        self._mtype += "Winners Finals"
        self._mtype += "Losers Finals"
        self._mtype += "Grand Finals"
        self._mtype += "Money Match"
        self._mtype += "Crew Battle"
        self._mtype += "Friendlies"
        chars = ['Fox', 'Falco', 'Marth', 'Sheik', 'Jigglypuff', 'Peach', 'Captain Falcon', 'Ice Climbers', 'Pikachu', 'Samus', 'Dr. Mario', 'Yoshi', 'Luigi', 'Ganondorf', 'Mario', 'Young Link', 'Donkey Kong', 'Link', 'Mr. Game & Watch', 'Mewtwo', 'Roy', 'Zelda', 'Ness', 'Pichu', 'Bowser', 'Kirby']
        self.minchars = {'Jigglypuff': "Puff", 'Captain Falcon': "Falcon", 'Ice Climbers': "Icies", 'Pikachu': "Pika", 'Dr. Mario': "Doc", 'Ganondorf': "Ganon", 'Young Link': "YLink", 'Donkey Kong': "DK", 'Mr. Game & Watch': "G&W", "Fox/Falco": "Spacies"}
        for char in chars:
            self._p1char += (char, False)
            self._p2char += (char, False)

        # Define the button action
        self._button.value = self.__buttonAction

        # Get latest values from form_values.txt
        try:
            with open(os.path.join(os.path.expanduser("~"), '.melee_form_values.json')) as f:
                i = 0
                values = json.loads(f.read())
                for val, var in zip(values, [self._ename, self._pID, self._mtype, self._p1, self._p2, self._p1char, self._p2char, self._bracket, self._file]):
                    if isinstance(val, (list, dict)):
                        var.load_form(dict(selected=val))
                    elif val:
                        var.value = val
                    i = i + 1
        except (IOError, OSError, StopIteration, json.decoder.JSONDecodeError) as e:
            print("No melee_form_values.json to read from, continuing with default values and creating file")
            with open(os.path.join(os.path.expanduser("~"), '.melee_form_values.json'), "w+") as f:  # if the file doesn't exist
                f.write(json.dumps(["No Data"]))

    def __buttonAction(self):
        """Button action event"""
        options = Namespace()
        row = [0] * 9
        options.ename = row[0] = self._ename.value
        f = self._pID.value.find("PL")
        self._pID.value = self._pID.value[f:f + 34]
        options.pID = row[1] = self._pID.value
        options.mtype = row[2] = self._mtype.value
        options.p1 = row[3] = self._p1.value
        options.p2 = row[4] = self._p2.value
        options.p1char = self._p1char.value
        options.p2char = self._p2char.value
        row[5] = deepcopy(self._p1char.value)
        row[6] = deepcopy(self._p2char.value)
        options.bracket = row[7] = self._bracket.value
        options.file = row[8] = self._file.value
        options.ignore = False
        self._p1char.load_form(dict(selected=[]))
        self._p2char.load_form(dict(selected=[]))
        self._p1.value = ""
        self._p2.value = ""
        self._qview += (options.p1, options.p2, options.mtype)
        self._queue.put(options)
        self._queueref.append(options)
        self._qview.resize_rows_contents()
        if self._firstrun:
            thr = threading.Thread(target=self.__worker)
            thr.daemon = True
            thr.start()
            self._firstrun = False
        with open(os.path.join(os.path.expanduser("~"), '.melee_form_values.json'), 'w') as f:
            f.write(json.dumps(row))

    def _init(self, opts):
        title = f"{opts.ename} - {opts.mtype} - ({'/'.join(opts.p1char)}) {opts.p1} vs {opts.p2} ({'/'.join(opts.p2char)})"
        if len(title) > 100:
            for i in range(len(opts.p1char)):
                if opts.p1char[i] in self.minchars:
                    opts.p1char[i] = self.minchars[opts.p1char[i]]
            for i in range(len(opts.p2char)):
                if opts.p2char[i] in self.minchars:
                    opts.p2char[i] = self.minchars[opts.p2char[i]]
        title = f"{opts.ename} - {opts.mtype} - ({'/'.join(opts.p1char)}) {opts.p1} vs {opts.p2} ({'/'.join(opts.p2char)})"
        if len(title) > 100:
            print("Title is greater than 100 characters after minifying character names")
            print(title)
            print("Killing this thread now\n\n")
            return
        print(f"Uploading {title}")
        credit = "Uploaded with Melee-Youtube-Uploader (https://github.com/NikhilNarayana/Melee-YouTube-Uploader) by Nikhil Narayana"
        descrip = (f"Bracket: {opts.bracket}\n\n" + credit) if opts.bracket else credit
        tags = ["Melee", "Super Smash Brothers Melee", "Smash Brother", "Super Smash Bros. Melee", "meleeuploader"]
        tags.extend((opts.p1char, opts.p2char, opts.ename, opts.p1, opts.p2))
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
            media_body=MediaFileUpload(opts.file,
                                       chunksize=104857600,
                                       resumable=True),)
        vid = self._upload(insert_request)
        self._youtube.playlistItems().insert(
            part="snippet",
            body=dict(
                snippet=dict(
                    playlistId=opts.pID,
                    resourceId=dict(
                        kind='youtube#video',
                        videoId=vid)))).execute()
        print("Added to playlist")
        print("DONE\n")

    def _upload(self, insert_request):
        response = None
        retry_exceptions = get_retry_exceptions()
        retry_status_codes = get_retry_status_codes()
        ACCEPTABLE_ERRNO = (errno.EPIPE, errno.EINVAL, errno.ECONNRESET)
        try:
            ACCEPTABLE_ERRNO += (errno.WSAECONNABORTED,)
        except AttributeError:
            pass  # Not windows
        while True:
            try:
                status, response = insert_request.next_chunk()
                if status is not None:
                    percent = Decimal(int(status.resumable_progress) / int(status.total_size))
                    print(f"{round(100 * percent, 2)}% uploaded")
            except HttpError as e:
                if e.resp.status in retry_status_codes:
                    print(f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}")
            except retry_exceptions as e:
                print(f"A retriable error occurred: {e}")

            except Exception as e:
                if e in ACCEPTABLE_ERRNO:
                    print("Retriable Error occured, retrying now")
                else:
                    print(e)
                pass
            if response:
                if "id" in response:
                    print(f"Video link is https://www.youtube.com/watch?v={response['id']}")
                    return response['id']
                else:
                    print(response)
                    print(status)
                    exit("Upload failed, no id in response")

    def writePrint(self, text):
        self._output.value += text
        self._output._form.plainTextEdit.moveCursor(QtGui.QTextCursor.End)
        print(text, file=sys.__stdout__, end='')

    def __reset_cred_event(self):
        os.remove(os.path.join(os.path.expanduser("~"), ".melee-oauth2-youtube.json"))
        # os.remove(os.path.join(os.path.expanduser("~"), ".melee-oauth2-spreadsheet.json"))
        sys.exit(0)

    def __worker(self):
        while True:
            options = self._queue.get()
            if not options.ignore:
                self._init(options)
                self._qview -= 0
                self._queueref.pop(0)
            self._queue.task_done()

    def __show_o_view(self, row, column):
        win = OptionsViewer(row, self._queueref[row])
        win.parent = self
        win.show()


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
        pyforms_lite.start_app(MeleeUploader, geometry=(100, 100, 1, 1))
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
