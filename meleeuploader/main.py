#!/usr/bin/env python3

import os
import sys
import json
import errno
import pickle
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

        # History
        self.__history = []

        # Filenames
        self.__form_values = os.path.join(os.path.expanduser("~"), '.melee_form_values.json')
        self.__queue_values = os.path.join(os.path.expanduser("~"), ".melee_queue_values.txt")

        # Queue
        self._queue = Queue()
        self._queueref = []
        self._firstrun = True
        self._stop_thread = False

        # Get YouTube
        self._youtube = get_youtube_service()

        # Create form fields
        # Event Values
        self._ename = ControlText("Event Name")
        self._pID = ControlText("Playlist ID")
        self._bracket = ControlText("Bracket Link")
        self._tags = ControlText("Tags")
        # Match Values
        self._file = ControlFile("File")
        self._p1 = ControlText()
        self._p2 = ControlText()
        self._p1sponsor = ControlText("P1", helptext="Sponsor Tag")
        self._p2sponsor = ControlText("P2", helptext="Sponsor Tag")
        self._p1char = ControlCheckBoxList("P1 Characters")
        self._p2char = ControlCheckBoxList("P2 Characters")
        self._mtype = ControlCombo()
        self._mextraleft = ControlText()
        self._mextraright = ControlText()

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
        self.formset = [{"-Match": ["_file", (' ', "_mextraleft", "_mtype", "_mextraright", ' '), (' ', "_p1sponsor", "_p1", ' '), (' ', "_p1char", ' '), (' ', "_p2sponsor", "_p2", ' '), (' ', "_p2char", ' ')],
                         "-Status-": ["_output", "=", "_qview"],
                         "Event-": ["_ename", "_pID", "_bracket", "_tags"]},
                        (' ', '_button', ' ')]

        # Main Menu Layout
        self.mainmenu = [
            {'Settings': [{'Save Form': self.__save_form}, {'Remove Youtube Credentials': self.__reset_cred_event}],
                'Clear': [{'Clear Match Values': self.__reset_match}, {'Clear Event Values': self.__reset_event}, {'Clear All': self.__reset_forms}],
                'Queue': [{'Toggle Queue': self.__toggle_worker}, {'Save Queue': self.__save_queue}, {'Load Queue': self.__load_queue}],
                'History': [{'Show History': self.__show_h_view}]}]

        # Add ControlCombo values
        self._mtype += "Pools"
        self._mtype += "Round Robin"
        self._mtype += "Winners"
        self._mtype += "Losers"
        self._mtype += "Winners Finals"
        self._mtype += "Losers Finals"
        self._mtype += "Grand Finals"
        self._mtype += "Money Match"
        self._mtype += "Crew Battle"
        self._mtype += "Friendlies"
        chars = ['Fox', 'Falco', 'Marth', 'Sheik', 'Jigglypuff', 'Peach', 'Captain Falcon', 'Ice Climbers', 'Pikachu', 'Samus', 'Dr. Mario', 'Yoshi', 'Luigi', 'Ganondorf', 'Mario', 'Young Link', 'Donkey Kong', 'Link', 'Mr. Game & Watch', 'Mewtwo', 'Roy', 'Zelda', 'Ness', 'Pichu', 'Bowser', 'Kirby']
        self.minchars = {'Jigglypuff': "Puff", 'Captain Falcon': "Falcon", 'Ice Climbers': "Icies", 'Pikachu': "Pika", 'Dr. Mario': "Doc", 'Ganondorf': "Ganon", 'Young Link': "YLink", 'Donkey Kong': "DK", 'Mr. Game & Watch': "G&W"}
        for char in chars:
            self._p1char += (char, False)
            self._p2char += (char, False)

        # Set placeholder text
        self._p1sponsor.form.lineEdit.setPlaceholderText("Sponsor Tag")
        self._p2sponsor.form.lineEdit.setPlaceholderText("Sponsor Tag")
        self._p1.form.lineEdit.setPlaceholderText("P1 Tag")
        self._p2.form.lineEdit.setPlaceholderText("P2 Tag")
        self._mextraleft.form.lineEdit.setPlaceholderText("Match Type Prefix")
        self._mextraright.form.lineEdit.setPlaceholderText("Match Type Suffix")
        self._bracket.form.lineEdit.setPlaceholderText("Include https://")
        self._tags.form.lineEdit.setPlaceholderText("Separate with commas")
        self._pID.form.lineEdit.setPlaceholderText("Accepts full YT link")

        # Define the button action
        self._button.value = self.__buttonAction

        # Get latest values from form_values.txt
        self.__load_form()

    def __buttonAction(self):
        """Button action event"""
        if any(not x for x in (self._ename.value, self._p1.value, self._p2.value, self._p1char.value, self._p2char.value, self._file.value)):
            print("Missing one of the required fields")
            return
        options = Namespace()
        self.__history.append(self.__save_form())
        options.ename = self._ename.value
        f = self._pID.value.find("PL")
        self._pID.value = self._pID.value[f:f + 34]
        options.pID = self._pID.value
        options.mtype = self._mtype.value
        options.p1 = self._p1.value
        options.p2 = self._p2.value
        options.p1char = self._p1char.value
        options.p2char = self._p2char.value
        options.bracket = self._bracket.value
        options.file = self._file.value
        options.tags = self._tags.value
        options.mextraright = self._mextraright.value
        options.mextraleft = self._mextraleft.value
        if self._p1sponsor.value:
            options.p1 = " | ".join((self._p1sponsor.value, options.p1))
        if self._p2sponsor.value:
            options.p2 = " | ".join((self._p2sponsor.value, options.p2))
        options.ignore = False
        self.__reset_match(False)
        self._qview += (options.p1, options.p2, " ".join((options.mextraleft, options.mtype, options.mextraright)))
        self._queue.put(options)
        self._queueref.append(options)
        self._qview.resize_rows_contents()
        if self._firstrun:
            thr = threading.Thread(target=self.__worker)
            thr.daemon = True
            thr.start()
            self._firstrun = False

    def _init(self, opts):
        if opts.mextraleft and opts.mextraright:
            opts.mtype = " ".join((opts.mextraleft, opts.mtype, opts.mextraright))
        elif opts.mextraleft:
            opts.mtype = " ".join((opts.mextraleft, opts.mtype))
        elif opts.mextraright:
            opts.mtype = " ".join((opts.mtype, opts.mextraright))
        title = f"{opts.ename} - {opts.mtype} - ({'/'.join(opts.p1char)}) {opts.p1} vs {opts.p2} ({'/'.join(opts.p2char)})"
        if len(title) > 100:
            for i in range(len(opts.p1char)):
                if opts.p1char[i] in self.minchars:
                    opts.p1char[i] = self.minchars[opts.p1char[i]]
            if all(x in opts.p1char for x in ("Fox", "Falco")):
                opts.p1char.remove("Fox")
                opts.p1char.remove("Falco")
                opts.p1char.insert(0, "Spacies")
            for i in range(len(opts.p2char)):
                if opts.p2char[i] in self.minchars:
                    opts.p2char[i] = self.minchars[opts.p2char[i]]
            if all(x in opts.p2char for x in ("Fox", "Falco")):
                opts.p2char.remove("Fox")
                opts.p2char.remove("Falco")
                opts.p2char.insert(0, "Spacies")
        title = f"{opts.ename} - {opts.mtype} - ({'/'.join(opts.p1char)}) {opts.p1} vs {opts.p2} ({'/'.join(opts.p2char)})"
        if len(title) > 100:
            print("Title is greater than 100 characters after minifying character names")
            print(title)
            print(len(title))
            print("Killing this thread now\n\n")
            return False
        print(f"Uploading {title}")
        credit = "Uploaded with Melee-Youtube-Uploader (https://github.com/NikhilNarayana/Melee-YouTube-Uploader) by Nikhil Narayana"
        descrip = (f"Bracket: {opts.bracket}\n\n{credit}") if opts.bracket else credit
        tags = ["Melee", "Super Smash Brothers Melee", "Smash Brothers", "Super Smash Bros. Melee", "meleeuploader"]
        tags.extend((opts.p1char, opts.p2char, opts.ename, opts.p1, opts.p2))
        if opts.tags:
            tags.extend([x.strip() for x in opts.tags.split(",")])
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
        ret, vid = self._upload(insert_request)
        if ret and opts.pID[:2] == "PL":
            self._youtube.playlistItems().insert(
                part="snippet",
                body=dict(
                    snippet=dict(
                        playlistId=opts.pID,
                        resourceId=dict(
                            kind='youtube#video',
                            videoId=vid)))).execute()
            print("Added to playlist")
        if ret:
            print("DONE\n")
        else:
            print(vid)
        return ret

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
                    return True, response['id']
                else:
                    print(response)
                    print(status)
                    return False, "Upload failed, no id in response"

    def writePrint(self, text):
        self._output.value += text
        self._output._form.plainTextEdit.moveCursor(QtGui.QTextCursor.End)
        print(text, file=sys.__stdout__, end='')

    def __reset_cred_event(self):
        os.remove(os.path.join(os.path.expanduser("~"), ".melee-oauth2-youtube.json"))
        # os.remove(os.path.join(os.path.expanduser("~"), ".melee-oauth2-spreadsheet.json"))
        sys.exit(0)

    def __reset_match(self, menu=True):
        self._file.value = ""
        self._p1char.load_form(dict(selected=[]))
        self._p2char.load_form(dict(selected=[]))
        self._p1.value = ""
        self._p2.value = ""
        self._p1sponsor.value = ""
        self._p2sponsor.value = ""
        self._file.value = ""
        self._mextraright.value = ""
        if menu:
            self._mextraleft.value = ""

    def __reset_event(self):
        self._ename.value = ""
        self._pID.value = ""
        self._bracket.value = ""
        self._tags.value = ""

    def __reset_forms(self):
        self.__reset_match()
        self.__reset_event()

    def __worker(self):
        while True:
            if self._stop_thread:
                print("Stopping Worker")
                while self._stop_thread:
                    sleep(1)
            options = self._queue.get()
            if not options.ignore:
                if self._init(options):
                    row = [None] * 14
                    f = self._pID.value.find("PL")
                    self._pID.value = self._pID.value[f:f + 34]
                    row[0] = deepcopy(self._ename.value)
                    row[1] = deepcopy(self._pID.value)
                    row[7] = deepcopy(self._bracket.value)
                    row[9] = deepcopy(self._tags.value)
                    row[11] = deepcopy(self._mextraleft.value)
                    with open(self.__form_values, 'w') as f:
                        f.write(json.dumps(row))
                self._qview -= 0
                self._queueref.pop(0)
            self._queue.task_done()

    def __show_o_view(self, row, column):
        win = OptionsViewer(row, self._queueref[row], self._stop_thread)
        win.parent = self
        win.show()

    def __show_h_view(self):
        win = HistoryViewer(self.__history, self._stop_thread, self)
        win.parent = self
        win.show()

    def __toggle_worker(self):
        if not self._stop_thread:
            print("Stopping Queue")
            self._stop_thread = True
            self._firstrun = False
        else:
            print("Starting Queue")
            self._stop_thread = False
            self._firstrun = True

    def __save_queue(self):
        with open(self.__queue_values, "wb") as f:
            f.write(pickle.dumps(self._queueref))

    def __load_queue(self):
        with open(self.__queue_values, "rb") as f:
            self._queueref = pickle.load(f)
        for options in self._queueref:
            self._qview += (options.p1, options.p2, options.mtype)
            self._queue.put(options)
            self._qview.resize_rows_contents()
            self.__history.append(self.__save_form(options))
        thr = threading.Thread(target=self.__worker)
        thr.daemon = True
        self._firstrun = False
        self._stop_thread = False
        thr.start()

    def __save_form(self, options=[]):
        row = [None] * 14
        if options:
            f = options.pID.find("PL")
            options.pID = options.pID[f:f + 34]
            row[0] = deepcopy(options.ename)
            row[1] = deepcopy(options.pID)
            row[2] = deepcopy(options.mtype)
            row[3] = deepcopy(options.p1)
            row[4] = deepcopy(options.p2)
            row[5] = deepcopy(options.p1char)
            row[6] = deepcopy(options.p2char)
            row[7] = deepcopy(options.bracket)
            row[8] = deepcopy(options.file)
            row[9] = deepcopy(options.tags)
            row[10] = deepcopy(options.mextraright)
            row[11] = deepcopy(options.mextraleft)
            row[12] = ""
            row[13] = ""
        else:
            f = self._pID.value.find("PL")
            self._pID.value = self._pID.value[f:f + 34]
            row[0] = deepcopy(self._ename.value)
            row[1] = deepcopy(self._pID.value)
            row[2] = deepcopy(self._mtype.value)
            row[3] = deepcopy(self._p1.value)
            row[4] = deepcopy(self._p2.value)
            row[5] = deepcopy(self._p1char.value)
            row[6] = deepcopy(self._p2char.value)
            row[7] = deepcopy(self._bracket.value)
            row[8] = deepcopy(self._file.value)
            row[9] = deepcopy(self._tags.value)
            row[10] = deepcopy(self._mextraright.value)
            row[11] = deepcopy(self._mextraleft.value)
            row[12] = deepcopy(self._p1sponsor.value)
            row[13] = deepcopy(self._p2sponsor.value)
        with open(self.__form_values, 'w') as f:
                f.write(json.dumps(row))
        return row

    def __load_form(self, history=[]):
        if history:
            for val, var in zip(history, [self._ename, self._pID, self._mtype, self._p1, self._p2, self._p1char, self._p2char, self._bracket, self._file, self._tags, self._mextraright, self._mextraleft, self._p1sponsor, self._p2sponsor]):
                if isinstance(val, (list, dict)):
                    var.load_form(dict(selected=val))
                elif val:
                    var.value = val
        else:
            try:
                with open(self.__form_values) as f:
                    values = json.loads(f.read())
                    for val, var in zip(values, [self._ename, self._pID, self._mtype, self._p1, self._p2, self._p1char, self._p2char, self._bracket, self._file, self._tags, self._mextraright, self._mextraleft, self._p1sponsor, self._p2sponsor]):
                        if isinstance(val, (list, dict)):
                            var.load_form(dict(selected=val))
                        elif val:
                            var.value = val
            except (IOError, OSError, StopIteration, json.decoder.JSONDecodeError) as e:
                print("No melee_form_values.json to read from, continuing with default values")


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
