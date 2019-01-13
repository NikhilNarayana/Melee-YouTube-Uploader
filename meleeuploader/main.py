#!/usr/bin/env python3

import os
import sys
import json
import errno
import pickle
import socket
import threading
import websocket
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
from obswebsocket import obsws, events
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from pyforms_lite.controls import ControlText, ControlFile
from pyforms_lite.controls import ControlTextArea, ControlList
from pyforms_lite.controls import ControlCombo, ControlProgress
from pyforms_lite.controls import ControlButton, ControlCheckBox, ControlCheckBoxList

melee = True


class EmittingStream(QtCore.QObject):

    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass


class MeleeUploader(BaseWidget):

    def __init__(self):
        global melee
        self._melee = melee
        if self._melee:
            super(MeleeUploader, self).__init__("Melee YouTube Uploader")
        else:
            super(MeleeUploader, self).__init__("Smash YouTube Uploader")
        # Redirct print output
        sys.stdout = EmittingStream(textWritten=self.writePrint)

        # Websocket
        self._ws = None

        # History
        self.__history = []

        # Filenames
        self.__form_values = os.path.join(os.path.expanduser("~"), '.melee_form_values.json')
        self.__queue_values = os.path.join(os.path.expanduser("~"), ".melee_queue_values.txt")
        self.__log_file = os.path.join(os.path.expanduser("~"), ".melee_log.txt")

        # Redirect error output to a file
        sys.stderr = open(self.__log_file, "a")

        # Queue
        self._queue = Queue()
        self._queueref = []
        self._firstrun = True
        self._stop_thread = False

        # Get YouTube
        self._youtube = get_youtube_service()

        # Create form fields
        # Event Values
        self._privacy = ControlCombo("Video Privacy")
        self._ename = ControlText("Event Name")
        self._ename_min = ControlText()
        self._pID = ControlText("Playlist ID")
        self._bracket = ControlText("Bracket Link")
        self._tags = ControlText("Tags")
        self._description = ControlTextArea("Description")
        # Match Values
        self._file = ControlFile("File")
        self._p1 = ControlText()
        self._p2 = ControlText()
        self._p1sponsor = ControlText("P1", helptext="Sponsor Tag")
        self._p2sponsor = ControlText("P2", helptext="Sponsor Tag")
        self._p1char = ControlCheckBoxList("P1 Characters")
        self._p2char = ControlCheckBoxList("P2 Characters")
        self._mtype = ControlCombo()
        self._mprefix = ControlText()
        self._msuffix = ControlText()

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
        self.formset = [{"-Match": ["_file", (' ', "_mprefix", "_mtype", "_msuffix", ' '), (' ', "_p1sponsor", "_p1", ' '), (' ', "_p1char", ' '), (' ', "_p2sponsor", "_p2", ' '), (' ', "_p2char", ' ')],
                         "-Status-": ["_output", "=", "_qview"],
                         "Event-": ["_privacy", ("_ename","_ename_min"), "_pID", "_bracket", "_tags", "_description"]},
                        (' ', '_button', ' ')]

        # Main Menu Layout
        self.mainmenu = [
            {'Settings': [{'Save Form': self.__save_form}, {'Remove YouTube Credentials': self.__reset_cred_event}, {'Toggle Websocket for SA': self.__toggle_websocket}, {'Hook into OBS': self.__hook_obs}],
                'Clear': [{'Clear Match Values': self.__reset_match}, {'Clear Event Values': self.__reset_event}, {'Clear All': self.__reset_forms}],
                'Queue': [{'Toggle Uploads': self.__toggle_worker}, {'Save Queue': self.__save_queue}, {'Load Queue': self.__load_queue}],
                'History': [{'Show History': self.__show_h_view}],
                'Characters': [{'Melee': self.__melee_chars}, {'Ultimate': self.__ultimate_chars}]}]

        # Add ControlCombo values
        self.__match_types = ["Pools", "Round Robin", "Winners", "Losers", "Winners Finals", "Losers Finals", "Grand Finals", "Money Match", "Crew Battle", "Ladder", "Friendlies"]
        for t in self.__match_types:
            self._mtype += t
        self.__min_match_types = {"Round ": "R", "Round Robin": "RR", "Winners Finals": "WF", "Losers Finals": "LF", "Grand Finals": "GF", "Money Match": "MM", "Crew Battle": "Crews", "Semifinals": "SF", "Quarterfinals": "QF"}
        self._privacy += "public"
        self._privacy += "unlisted"
        self._privacy += "private"

        # Character Names and Minifications
        self.minchars = {
            'Jigglypuff': "Puff",
            'Captain Falcon': "Falcon",
            'Ice Climbers': "Icies",
            'Pikachu': "Pika",
            'Dr. Mario': "Doc",
            'Ganondorf': "Ganon",
            'Young Link': "YLink",
            'Donkey Kong': "DK",
            'Mr. Game & Watch': "G&W",
            'Mewtwo': "Mew2",
            'Dark Samus': "D. Samus",
            'Meta Knight': "MK",
            'Dark Pit': "D. Pit",
            'Zero Suit Samus': "ZSS",
            'Pokemon Trainer': "PK Trainer",
            'Diddy Kong': "Diddy",
            'King Dedede': "DDD",
            'Toon Link': "TLink",
            'Wii Fit Trainer': "Wii Fit",
            'Rosalina & Luma': "Rosa",
            'Mii Fighter': "Mii",
            'Bayonetta': "Bayo",
            'King K. Rool': "K. Rool",
            'Piranha Plant': "Plant"
        }
        self._melee_chars = [
            'Fox', 'Falco', 'Marth', 'Sheik', 'Jigglypuff', 'Peach', 'Captain Falcon',
            'Ice Climbers', 'Pikachu', 'Samus', 'Dr. Mario', 'Yoshi', 'Luigi',
            'Ganondorf', 'Mario', 'Young Link', 'Donkey Kong', 'Link',
            'Mr. Game & Watch', 'Mewtwo', 'Roy', 'Zelda', 'Ness', 'Pichu', 'Bowser',
            'Kirby'
        ]
        self._ult_chars = [
            'Mario', 'Donkey Kong', 'Link', 'Samus', 'Dark Samus', 'Yoshi', 'Fox',
            'Pikachu', 'Luigi', 'Ness', 'Captain Falcon', 'Jigglypuff', 'Peach',
            'Daisy', 'Bowser', 'Ice Climbers', 'Sheik', 'Zelda', 'Dr. Mario', 'Pichu',
            'Falco', 'Marth', 'Lucina', 'Young Link', 'Ganondorf', 'Mewtwo', 'Roy',
            'Chrom', 'Mr. Game & Watch', 'Meta Knight', 'Pit', 'Dark Pit',
            'Zero Suit Samus', 'Wario', 'Snake', 'Ike', 'Pokemon Trainer',
            'Diddy Kong', 'Lucas', 'Sonic', 'King Dedede', 'Olimar', 'Lucario',
            'R.O.B', 'Toon Link', 'Wolf', 'Villager', 'Mega Man', 'Wii Fit Trainer',
            'Rosalina & Luma', 'Little Mac', 'Greninja', 'Mii Fighter', 'Palutena',
            'Pac-Man', 'Robin', 'Shulk', 'Bowser Jr.', 'Duck Hunt', 'Ryu', 'Ken',
            'Cloud', 'Corrin', 'Bayonetta', 'Inkling', 'Ridley', 'Simon', 'Richter',
            'King K. Rool', 'Isabelle', 'Incineroar', 'Piranha Plant', 'Joker'
        ]

        # Set placeholder text
        self._ename_min.form.lineEdit.setPlaceholderText("Shortened Event Name")
        self._p1sponsor.form.lineEdit.setPlaceholderText("Sponsor Tag")
        self._p2sponsor.form.lineEdit.setPlaceholderText("Sponsor Tag")
        self._p1.form.lineEdit.setPlaceholderText("P1 Tag")
        self._p2.form.lineEdit.setPlaceholderText("P2 Tag")
        self._mprefix.form.lineEdit.setPlaceholderText("Match Type Prefix")
        self._msuffix.form.lineEdit.setPlaceholderText("Match Type Suffix")
        self._bracket.form.lineEdit.setPlaceholderText("Include https://")
        self._tags.form.lineEdit.setPlaceholderText("Separate with commas")
        self._pID.form.lineEdit.setPlaceholderText("Accepts full YT link")

        # Define the button action
        self._button.value = self.__buttonAction

        # Define the existing form fields
        self._form_fields = [
            self._ename, self._pID, self._mtype, self._p1, self._p2, self._p1char,
            self._p2char, self._bracket, self._file, self._tags, self._msuffix,
            self._mprefix, self._p1sponsor, self._p2sponsor, self._privacy,
            self._description, self._ename_min
        ]

        # Set character list
        if self._melee:
            self.__melee_chars()
        else:
            self.__ultimate_chars()

        # Get latest values from form_values.txt
        self.__load_form()

    def __buttonAction(self, data=None):
        """Button action event"""
        if any(not x for x in (self._ename.value, self._p1.value, self._p2.value, self._file.value)):
            print("Missing one of the required fields (event name, player names, file name)")
            return
        options = Namespace()
        self.__history.append(self.__save_form())
        options.ename = self._ename.value
        if self._ename_min.value:
            options.ename_min = self._ename_min.value
        else:
            options.ename_min = options.ename
        f = self._pID.value.find("PL")
        self._pID.value = self._pID.value[f:f + 34]
        options.pID = self._pID.value
        options.mtype = self._mtype.value
        options.mmid = options.mtype
        options.p1 = self._p1.value
        options.p2 = self._p2.value
        options.p1char = self._p1char.value
        options.p2char = self._p2char.value
        options.bracket = self._bracket.value
        isdir = os.path.isdir(self._file.value)
        if isdir:
            options.file = max([os.path.join(self._file.value,f) for f in os.listdir(self._file.value) if os.path.isfile(os.path.join(self._file.value, f))], key=os.path.getctime)
        else:
            options.file = self._file.value
        options.tags = self._tags.value
        options.msuffix = self._msuffix.value
        options.mprefix = self._mprefix.value
        options.privacy = self._privacy.value
        options.descrip = self._description.value
        if self._p1sponsor.value:
            options.p1 = " | ".join((self._p1sponsor.value, options.p1))
        if self._p2sponsor.value:
            options.p2 = " | ".join((self._p2sponsor.value, options.p2))
        options.ignore = False
        self.__reset_match(False, isdir)
        self._qview += (options.p1, options.p2, " ".join((options.mprefix, options.mtype, options.msuffix)))
        self._queue.put(options)
        self._queueref.append(options)
        self._qview.resize_rows_contents()
        if self._firstrun:
            thr = threading.Thread(target=self.__worker)
            thr.daemon = True
            thr.start()
            self._firstrun = False

    def _init(self, opts):
        if opts.mprefix and opts.msuffix:
            opts.mtype = " ".join((opts.mprefix, opts.mtype, opts.msuffix))
        elif opts.mprefix:
            opts.mtype = " ".join((opts.mprefix, opts.mtype))
        elif opts.msuffix:
            opts.mtype = " ".join((opts.mtype, opts.msuffix))
        chars_exist = all(x for x in [opts.p1char, opts.p2char])
        title = f"{opts.ename} - {opts.mtype} - ({'/'.join(opts.p1char)}) {opts.p1} vs {opts.p2} ({'/'.join(opts.p2char)})" if chars_exist else f"{opts.ename} - {opts.mtype} - {opts.p1} vs {opts.p2}"
        if len(title) > 100:
            opts.p1char = self._minify_chars(opts.p1char)
            opts.p2char = self._minify_chars(opts.p2char)
            title = f"{opts.ename} - {opts.mtype} - ({'/'.join(opts.p1char)}) {opts.p1} vs {opts.p2} ({'/'.join(opts.p2char)})" if chars_exist else f"{opts.ename} - {opts.mtype} - {opts.p1} vs {opts.p2}"
            if len(title) > 100:
                opts.mtype = self._minify_mtype(opts)
                title = f"{opts.ename} - {opts.mtype} - ({'/'.join(opts.p1char)}) {opts.p1} vs {opts.p2} ({'/'.join(opts.p2char)})" if chars_exist else f"{opts.ename} - {opts.mtype} - {opts.p1} vs {opts.p2}"
                if len(title) > 100:
                    opts.mtype = self._minify_mtype(opts, True)
                    title = f"{opts.ename} - {opts.mtype} - ({'/'.join(opts.p1char)}) {opts.p1} vs {opts.p2} ({'/'.join(opts.p2char)})" if chars_exist else f"{opts.ename} - {opts.mtype} - {opts.p1} vs {opts.p2}"
                    if len(title) > 100:
                        title = f"{opts.ename_min} - {opts.mtype} - ({'/'.join(opts.p1char)}) {opts.p1} vs {opts.p2} ({'/'.join(opts.p2char)})" if chars_exist else f"{opts.ename_min} - {opts.mtype} - {opts.p1} vs {opts.p2}"
                        if len(title) > 100:
                            # I can only hope no one ever goes this far
                            print("Title is greater than 100 characters after minifying all options")
                            print(title)
                            print("Title Length: " + len(title))
                            print("Killing this upload now\n\n")
                            return False
        print(f"Uploading {title}")
        credit = "Uploaded with Melee-YouTube-Uploader (https://github.com/NikhilNarayana/Melee-YouTube-Uploader) by Nikhil Narayana"
        if opts.descrip:
            descrip = f"Bracket: {opts.bracket}\n{opts.descrip}\n\n{credit}" if opts.bracket else f"{opts.descrip}\n\n{credit}"
        else:
            descrip = f"Bracket: {opts.bracket}\n\n{credit}" if opts.bracket else credit
        tags = ["Melee", "Super Smash Brothers Melee", "Smash Brothers", "Super Smash Bros. Melee", "meleeuploader", "SSBM", "ssbm"] if self._melee else ["Ultimate", "Super Smash Brothers Ultimate", "Smash Brothers", "Super Smash Bros. Ultimate", "smashuploader", "SSBU", "ssbu"]
        tags.extend((opts.p1char, opts.p2char, opts.ename, opts.ename_min, opts.p1, opts.p2))
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
                privacyStatus=opts.privacy)
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
        if sys.__stdout__:
            print(text, file=sys.__stdout__, end='')

    def __reset_cred_event(self):
        os.remove(os.path.join(os.path.expanduser("~"), ".melee-oauth2-youtube.json"))
        # os.remove(os.path.join(os.path.expanduser("~"), ".melee-oauth2-spreadsheet.json"))
        sys.exit(0)

    def __reset_match(self, menu=True, isdir=False):
        if not isdir:
            self._file.value = ""
        self._p1char.load_form(dict(selected=[]))
        self._p2char.load_form(dict(selected=[]))
        self._p1.value = ""
        self._p2.value = ""
        self._p1sponsor.value = ""
        self._p2sponsor.value = ""
        self._file.value = ""
        self._msuffix.value = ""
        if menu:
            self._mtype.value = "Pools"
            self._mprefix.value = ""

    def __reset_event(self):
        self._privacy.value = "public"
        self._ename.value = ""
        self._ename_min.value = ""
        self._pID.value = ""
        self._bracket.value = ""
        self._tags.value = ""
        self._description.value = ""

    def __reset_forms(self):
        self.__reset_match()
        self.__reset_event()

    def __worker(self):
        while True:
            if self._stop_thread:
                print("Stopping Upload Service")
                break
            options = self._queue.get()
            if not options.ignore:
                if self._init(options):
                    row = [None] * 20
                    f = self._pID.value.find("PL")
                    self._pID.value = self._pID.value[f:f + 34]
                    row[0] = deepcopy(options.ename)
                    row[1] = deepcopy(options.pID)
                    row[7] = deepcopy(options.bracket)
                    row[9] = deepcopy(options.tags)
                    row[11] = deepcopy(options.mprefix)
                    row[14] = deepcopy(options.privacy)
                    row[16] = deepcopy(options.ename_min)
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
            print("Stopping Uploads")
            self._stop_thread = True
            self._firstrun = False
        else:
            print("Ready to Upload")
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
        row = [None] * 20
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
            row[10] = deepcopy(options.msuffix)
            row[11] = deepcopy(options.mprefix)
            row[12] = ""
            row[13] = ""
            row[14] = deepcopy(options.privacy)
            row[15] = deepcopy(options.descrip)
            row[16] = deepcopy(options.ename_min)
        else:
            f = self._pID.value.find("PL")
            self._pID.value = self._pID.value[f:f + 34]
            for i, var in zip(range(20), self._form_fields):
                row[i] = deepcopy(var.value)
        with open(self.__form_values, 'w') as f:
                f.write(json.dumps(row))
        return row

    def __load_form(self, history=[]):
        updateChars = True
        if history:
            for val, var in zip(history, self._form_fields):
                if isinstance(val, (list, dict)):
                    var.load_form(dict(selected=val))
                elif val:
                    var.value = val
        else:
            try:
                with open(self.__form_values) as f:
                    values = json.loads(f.read())
                    for val, var in zip(values, self._form_fields):
                        if isinstance(val, (list, dict)):
                            var.load_form(dict(selected=val))
                        elif val:
                            var.value = val
            except (IOError, OSError, StopIteration, json.decoder.JSONDecodeError) as e:
                print("No melee_form_values.json to read from, continuing with default values")

    def __melee_chars(self):
        self.__update_chars(self._melee_chars)

    def __ultimate_chars(self):
        self._melee = False
        self.__update_chars(self._ult_chars)

    def __update_chars(self, chars):
        p1 = self._p1char.value
        p2 = self._p2char.value
        self._p1char.clear()
        self._p2char.clear()
        for char in chars:
            self._p1char += (char, False)
            self._p2char += (char, False)
        self._p1char.load_form(dict(selected=p1))
        self._p2char.load_form(dict(selected=p2))

    def __update_form(self, message):
        data = json.loads(message)
        try:
            self._p1.value = data['player1']
            self._p2.value = data['player2']
            print(data['match'])
            for t in self.__match_types:
                if t.lower() in data['match'].lower():
                    self._mtype.value = t
                    if not data['match'].find(t):
                        sections = data['match'].split(t)
                        self._msuffix.value = sections[1].strip()
                    else:
                        sections = data['match'].split(t)
                        print(sections)
                        self._mprefix.value = sections[0].strip()
                        self._msuffix.value = sections[1].strip()
        except Exception as e:
            pass

    def __toggle_websocket(self):
        if self._ws is None:
            print("Starting Websocket, please make sure Scoreboard Assistant is open")
            self._ws = websocket.WebSocketApp("ws://localhost:58341", on_message=self.__update_form)
            self._wst = threading.Thread(target=self._ws.run_forever)
            self._wst.daemon = True
            self._wst.start()
        else:
            print("Closing the Websocket")
            self._ws.close()
            self._ws = None
            self._wst.join()

    def __hook_obs(self):
        self._obs = obsws("localhost", "4444")
        self._obs.register(self.__buttonAction, events.RecordingStopped)
        self._obs.connect()
        print("Hooked into OBS")

    def _minify_chars(self, pchars):
        for i in range(len(pchars)):
            if pchars[i] in self.minchars:
                pchars[i] = self.minchars[pchars[i]]
        if all(x in pchars for x in ("Fox", "Falco")):
            pchars.remove("Fox")
            pchars.remove("Falco")
            pchars.insert(0, "Spacies")
        return pchars

    def _minify_mtype(self, opts, middle=False):
        for k, v in self.__min_match_types.items():
            opts.mprefix = opts.mprefix.replace(k, v)
            opts.mprefix = opts.mprefix.replace(k.lower(), v)
            opts.msuffix = opts.msuffix.replace(k, v)
            opts.msuffix = opts.msuffix.replace(k.lower(), v)
            if middle:
                opts.mmid = opts.mmid.replace(k, v)
                opts.mmid = opts.mmid.replace(k.lower(), v)
        if opts.mprefix and opts.msuffix:
            opts.mtype = " ".join((opts.mprefix, opts.mmid, opts.msuffix))
        elif opts.mprefix:
            opts.mtype = " ".join((opts.mprefix, opts.mmid))
        elif opts.msuffix:
            opts.mtype = " ".join((opts.mmid, opts.msuffix))
        else:
            opts.mtype = opts.mmid
        return opts.mtype



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
        pyforms_lite.start_app(MeleeUploader, geometry=(200, 200, 1, 1))
        sys.exit(0)
    else:
        sys.exit(1)


def ult():
    global melee
    melee = False
    main()


if __name__ == "__main__":
    main()
