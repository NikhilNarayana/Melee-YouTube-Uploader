#!/usr/bin/env python3

import os
import sys
import json
import pickle
import threading
import subprocess
from queue import Queue
from copy import deepcopy
from datetime import datetime
from distutils.version import StrictVersion as sv

from . import utils
from . import consts
from . import workers
from .viewers import *

import requests
import websocket
import pyforms_lite
from argparse import Namespace
from PyQt5 import QtCore, QtGui
from pyforms_lite import BaseWidget
from pyforms_lite.controls import ControlText, ControlFile
from pyforms_lite.controls import ControlTextArea, ControlList
from pyforms_lite.controls import ControlCombo, ControlProgress
from pyforms_lite.controls import ControlButton, ControlCheckBox, ControlCheckBoxList


class SAHostPortInput(BaseWidget):
    def __init__(self):
        super(SAHostPortInput, self).__init__("SA Websocket")
        self._host = ControlText("Host IP")
        self._port = ControlText("Host Port")
        self._host.value = "localhost"
        self._port.value = "58341"
        self._button = ControlButton("Submit")
        self.formset = ["_host", "_port", "_button"]
        self._button.value = self.__button_action

    def __button_action(self):
        if self._host.value and self._port.value:
            self.parent._MeleeUploader__hook_sa(self._host.value, self._port.value)
        else:
            print("You must input a host IP and port number")


class OBSHostPortInput(BaseWidget):
    def __init__(self):
        super(OBSHostPortInput, self).__init__("OBS Websocket")
        self._host = ControlText("Host IP")
        self._port = ControlText("Host Port")
        self._host.value = "localhost"
        self._port.value = "4444"
        self._button = ControlButton("Submit")
        self.formset = ["_host", "_port", "_button"]
        self._button.value = self.__button_action

    def __button_action(self):
        if self._host.value and self._port.value:
            self.parent._MeleeUploader__hook_obs(self._host.value, self._port.value)
        else:
            print("You must input a host IP and port number")


class SCFileInput(BaseWidget):
    def __init__(self, f=""):
        super(SCFileInput, self).__init__("Stream Control")
        self._file = ControlFile("File")
        self.formset = ["_file", "_button"]
        self._button = ControlButton('Submit')

        self._file.value = f.value

        self._file.form.lineEdit.setPlaceholderText("Find your streamcontrol.json")

        self._button.value = self.__button_action

    def __button_action(self, data=None):
        if self._file.value:
            self.parent._MeleeUploader__hook_sc(self._file.value)
        else:
            print("You must select a file")


class MeleeUploader(BaseWidget):
    def __init__(self):
        try:  # check if the user can update the app
            latest_version = requests.get('https://pypi.org/pypi/MeleeUploader/json').json()['info']['version']
            if sv(latest_version) > sv(consts.__version__):  # prevents messages when developing
                if "linux" in sys.platform:
                    self.info(f"Current Version: {consts.__version__}\nVersion {latest_version} is available.\nUse sudo pip3 install -U meleeuploader=={latest_version} in terminal to update to the newest verison", title="MeleeUploader")
                else:
                    resp = self.question(f"Current Version: {consts.__version__}\nVersion {latest_version} is available. Would you like to update?", title="MeleeUploader")
                    if resp == "yes":
                        subprocess.call(('pip3', 'install', '-U', f'meleeuploader=={latest_version}'))
                        self.info("You can now restart the app to use the new version", title="MeleeUploader")
        except Exception as e:
            print(e)

        if consts.melee:
            super(MeleeUploader, self).__init__("Melee YouTube Uploader")
        else:
            super(MeleeUploader, self).__init__("Smash YouTube Uploader")

        # Redirct print output
        sys.stdout = workers.WriteWorker(textWritten=self.write_print)

        # Redirect error output to window, console, and file
        sys.stderr = workers.WriteWorker(textWritten=self.write_err)

        # Websocket
        self._sa = None
        self._obs = None

        # History
        self.__history = []

        # Queue
        self._queue = Queue()
        self._queueref = []

        # Event Values
        self._privacy = ControlCombo("Video Privacy")
        self._titleformat = ControlCombo("Title Format")
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
        self._p1sponsor = ControlText("P1")
        self._p2sponsor = ControlText("P2")
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
        self._qview.horizontal_headers = ["Player 1", "Player 2", "Round"]

        # Button
        self._button = ControlButton('Submit')
        self._button.value = self.__button_action

        # Title Formats
        for f in consts.titleformat:
            self._titleformat += f

        # Form Layout
        self.formset = [{"-Match": ["_file", (' ', "_mprefix", "_mtype", "_msuffix", ' '), (' ', "_p1sponsor", "_p1", ' '), (' ', "_p1char", ' '), (' ', "_p2sponsor", "_p2", ' '), (' ', "_p2char", ' ')],
                         "-Status-": ["_output", "=", "_qview"],
                         "Event-": ["_privacy", "_titleformat", ("_ename", "_ename_min"), "_pID", "_bracket", "_tags", "_description"]},
                        (' ', '_button', ' ')]

        # Main Menu Layout
        self.mainmenu = [
            {'Settings': [{'YouTube Log Out': self.__reset_cred}, {'Toggle SA Hook': self.__show_sa_form}, {'Toggle OBS Hook': self.__show_obs_form}, {'Toggle SC Hook': self.__show_sc_form}],
                'Save/Clear': [{'Save Form': self.__save_form}, {'Clear Match Values': self.__reset_match}, {'Clear Event Values': self.__reset_event}, {'Clear All': self.__reset_forms}],
                'Queue': [{'Toggle Uploads': utils.toggle_worker}, {'Save Queue': self.__save_queue}, {'Load Queue': self.__load_queue}],
                'History': [{'Show History': self.__show_h_view}],
                'Characters': [{'Melee': self.__melee_chars}, {'Ultimate': self.__ultimate_chars}, {'Custom': self.__custom_chars}]}]

        # Add ControlCombo values
        for t in consts.match_types:
            self._mtype += t
        for t in ("public", "unlisted", "private"):
            self._privacy += t

        # Set placeholder text
        self._ename_min.form.lineEdit.setPlaceholderText("Shortened Event Name")
        self._p1sponsor.form.lineEdit.setPlaceholderText("Sponsor Tag")
        self._p2sponsor.form.lineEdit.setPlaceholderText("Sponsor Tag")
        self._p1.form.lineEdit.setPlaceholderText("P1 Tag")
        self._p2.form.lineEdit.setPlaceholderText("P2 Tag")
        self._mprefix.form.lineEdit.setPlaceholderText("Round Prefix")
        self._msuffix.form.lineEdit.setPlaceholderText("Round Suffix")
        self._bracket.form.lineEdit.setPlaceholderText("Include https://")
        self._tags.form.lineEdit.setPlaceholderText("Separate with commas")
        self._pID.form.lineEdit.setPlaceholderText("Accepts full YT link")

        # For pulling characters
        self.__p1chars = []
        self.__p2chars = []

        # Set character list
        if consts.melee:
            self.__melee_chars()
        else:
            self.__ultimate_chars()

        # Stream Control
        self._sc = None
        self._scf = ControlText()

        # Define the existing form fields
        self._form_fields = (
            self._ename, self._pID, self._mtype, self._p1, self._p2, self._p1char,
            self._p2char, self._bracket, self._file, self._tags, self._msuffix,
            self._mprefix, self._p1sponsor, self._p2sponsor, self._privacy,
            self._description, self._ename_min, self._titleformat, self._scf,
        )

        # Get latest values from form_values.txt
        self.__load_form()

    def __button_action(self, data=None):
        """Button action event"""
        if any(not x for x in (self._ename.value, self._p1.value, self._p2.value, self._file.value)):
            print("Missing one of the required fields (event name, player names, file name)")
            return
        self.__p1chars = []
        self.__p2chars = []
        options = Namespace()
        self.__history.append(self.__save_form())
        options.ename = self._ename.value
        if self._ename_min.value:
            options.ename_min = self._ename_min.value
        else:
            options.ename_min = options.ename
        options.pID = self._pID.value
        options.mtype = self._mtype.value
        options.mmid = options.mtype
        options.p1 = self._p1.value
        options.p2 = self._p2.value
        options.p1char = self._p1char.value
        options.p2char = self._p2char.value
        options.bracket = self._bracket.value
        isadir = os.path.isdir(self._file.value)
        if isadir:
            options.file = max([os.path.join(self._file.value, f) for f in os.listdir(self._file.value) if os.path.isfile(os.path.join(self._file.value, f))], key=os.path.getmtime)
        else:
            options.file = self._file.value
        options.tags = self._tags.value
        options.msuffix = self._msuffix.value
        options.mprefix = self._mprefix.value
        options.privacy = self._privacy.value
        options.descrip = self._description.value
        options.titleformat = self._titleformat.value
        if self._p1sponsor.value:
            options.p1 = " | ".join((self._p1sponsor.value, options.p1))
        if self._p2sponsor.value:
            options.p2 = " | ".join((self._p2sponsor.value, options.p2))
        options.ignore = False
        self.__reset_match(False, isadir)
        self.__add_to_qview(options)
        self._queueref.append(options)
        if consts.firstrun:
            thr = threading.Thread(target=self.__worker)
            thr.daemon = True
            thr.start()
            consts.firstrun = False

    def write_print(self, text):
        self._output.value += text
        self._output._form.plainTextEdit.moveCursor(QtGui.QTextCursor.End)
        if sys.__stdout__:
            print(text, file=sys.__stdout__, end='')

    def write_err(self, text):
        self._output.value += text
        self._output._form.plainTextEdit.moveCursor(QtGui.QTextCursor.End)
        if sys.__stdout__:
            print(text, file=sys.__stdout__, end='')
        with open(consts.log_file, "a") as f:
            f.write(text)

    def __reset_cred(self):
        title = consts.youtube.channels().list(part='snippet', mine=True).execute()
        title = title['items'][0]['snippet']['title']
        resp = self.question(f"You are currently logged into {title}\nWould you like to log out?", title="MeleeUploader")
        if resp == "yes":
            if consts.youtube:
                os.remove(os.path.join(os.path.expanduser("~"), ".smash-oauth2-youtube.json"))
            if consts.sheets:
                os.remove(os.path.join(os.path.expanduser("~"), ".smash-oauth2-spreadsheet.json"))
            sys.exit(0)

    def __reset_match(self, menu=True, isadir=False):
        self._p1char.load_form(dict(selected=[]))
        self._p2char.load_form(dict(selected=[]))
        self._p1.value = ""
        self._p2.value = ""
        self._p1sponsor.value = ""
        self._p2sponsor.value = ""
        self._msuffix.value = ""
        if menu:
            isadir = os.path.isdir(self._file.value)
            if not isadir:
                self._file.value = ""
            self._mtype.value = "Pools"
            self._mprefix.value = ""
        else:
            if not isadir:
                self._file.value = ""

    def __reset_event(self):
        self._privacy.value = "public"
        self._titleformat.value = "{ename} - {round} - {p1} ({p1char}) vs {p2} ({p2char})"
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
        while not consts.stop_thread:
            options = self._queue.get()
            if not options.ignore:
                options.then = datetime.now()
                if utils.pre_upload(options):
                    row = [None] * 20
                    row[0] = deepcopy(options.ename)
                    row[1] = deepcopy(options.pID)
                    row[7] = deepcopy(options.bracket)
                    row[9] = deepcopy(options.tags)
                    row[11] = deepcopy(options.mprefix)
                    row[14] = deepcopy(options.privacy)
                    row[15] = deepcopy(options.descrip)
                    row[16] = deepcopy(options.ename_min)
                    row[17] = deepcopy(options.titleformat)
                    with open(consts.form_values, 'w') as f:
                        f.write(json.dumps(row))
                self._queueref.pop(0)
            self._qview -= 0
            self._queue.task_done()
        print("Stopping Upload Service")

    def __show_sa_form(self):
        if self._sa:
            self._sa.closews()
            print("Unhooked from SA")
            self._sat.quit()
            self._sa = None
        else:
            self._sawin = SAHostPortInput()
            self._sawin.parent = self
            self._sawin.show()

    def __show_obs_form(self):
        if self._obs:
            self._obs.closeobs()
            print("Unhooked from OBS")
            self._obst.quit()
            self._obs = None
        else:
            self._obswin = OBSHostPortInput()
            self._obswin.parent = self
            self._obswin.show()

    def __show_sc_form(self):
        if self._sc:
            self._sc.stopsc()
            print("Unhooked from SC")
            self._sct.quit()
            self._sc = None
        else:
            self._scrun = True
            self._scwin = SCFileInput(self._scf)
            self._scwin.parent = self
            self._scwin.show()

    def __hook_sa(self, host, port):
        self._sawin.close()
        self.warning("Please make sure Scoreboard Assistant is open", title="MeleeUploader")
        self._sa = workers.SAWorker(f"ws://{host}:{port}")
        self._sat = QtCore.QThread()
        self._sa.moveToThread(self._sat)
        self._sa.sig.connect(self.__sa_update)
        self._sat.started.connect(self._sa.startws)
        self._sat.start()
        print("Hooked into SA")

    def __hook_obs(self, host, port):
        self._obswin.close()
        self.warning("Please make sure OBS is open and the Websocket server is enabled with the default settings and no password", title="MeleeUploader")
        self._obs = workers.OBSWorker(host, port)
        self._obst = QtCore.QThread()
        self._obs.moveToThread(self._obst)
        self._obs.sig.connect(self.__button_action)
        self._obst.started.connect(self._obs.startobs)
        self._obst.start()
        print("Hooked into OBS")

    def __hook_sc(self, f):
        self._scwin.close()
        self._scf.value = f
        self._sc = workers.SCWorker(f)
        self._sct = QtCore.QThread()
        self._sc.moveToThread(self._sct)
        self._sc.sig.connect(self.__sc_update)
        self._sct.started.connect(self._sc.get_update)
        self._sct.start()
        print("Hooked into SC")

    def __show_o_view(self, row, column):
        win = OptionsViewer(row, self._queueref[row])
        win.parent = self
        win.show()

    def __show_h_view(self):
        self._hwin = HistoryViewer(self.__history)
        self._hwin.parent = self
        self._hwin.show()

    def __add_to_qview(self, options):
        self._qview += (options.p1, options.p2, " ".join((options.mprefix, options.mtype, options.msuffix)))
        self._queue.put(options)
        self._qview.resize_rows_contents()

    def __save_queue(self):
        if os.path.exists(consts.queue_values):
            resp = self.question(f"A queue already exists would you like to overwrite it?\nIt was last modified on {datetime.utcfromtimestamp(int(os.path.getmtime(consts.queue_values))).strftime('%Y-%m-%d')}")
            if resp == "yes":
                with open(consts.queue_values, "wb") as f:
                    f.write(pickle.dumps(self._queueref))
                print("Saved Queue, you can now close the program")
            elif resp == "no":
                resp = self.question("Would you like to add onto the end of that queue?")
                if resp == "yes":
                    queueref = None
                    with open(consts.queue_values, "rb") as f:
                        queueref = pickle.load(f)
                    queueref.extend(self._queueref)
                    with open(consts.queue_values, "wb") as f:
                        f.write(pickle.dumps(queueref))
                    print("Saved Queue, you can now close the program")
                else:
                    self.alert("Not saving queue")

    def __load_queue(self):
        if self._queueref:
            resp = self.question("Would you like to add to the existing queue?\nItems will be added to the front of the queue.")
            if resp == "yes":
                try:
                    with open(consts.queue_values, "rb") as f:
                        queueref = pickle.load(f)
                    queueref.extend(self._queueref)
                    self._queueref = queueref
                    self._qview.clear()
                    self._qview.horizontal_headers = ["Player 1", "Player 2", "Round"]
                    for options in self._queueref:
                        self.__add_to_qview(options)
                        self.__history.append(self.__save_form(options))
                except Exception as e:
                    print("You need to save a queue before loading a queue")
                    return
        else:
            try:
                with open(consts.queue_values, "rb") as f:
                    self._queueref = pickle.load(f)
                for options in self._queueref:
                    self.__add_to_qview(options)
                    self.__history.append(self.__save_form(options))
            except Exception as e:
                print("You need to save a queue before loading a queue")
                return

        resp = self.question("Do you want to start uploading?")
        if resp == "yes":
            thr = threading.Thread(target=self.__worker)
            thr.daemon = True
            consts.firstrun = False
            consts.stop_thread = False
            thr.start()

    def __save_form(self, options=[]):
        row = [None] * (len(self._form_fields) + 1)
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
            row[17] = deepcopy(options.titleformat)
            row[18] = deepcopy(self._scf.value)
        else:
            f = self._pID.value.find("PL")
            self._pID.value = self._pID.value[f:f + 34]
            for i, var in zip(range(len(self._form_fields) + 1), self._form_fields):
                row[i] = deepcopy(var.value)
        with open(consts.form_values, 'w') as f:
                f.write(json.dumps(row))
        return row

    def __load_form(self, history=[]):
        if history:
            self._hwin.close()
            for val, var in zip(history, self._form_fields):
                if isinstance(val, (list, dict)):
                    var.load_form(dict(selected=val))
                elif val:
                    var.value = val
        else:
            try:
                with open(consts.form_values, "r") as f:
                    values = json.loads(f.read())
                    for val, var in zip(values, self._form_fields):
                        if isinstance(val, (list, dict)):
                            var.load_form(dict(selected=val))
                        elif val:
                            var.value = val
            except (IOError, OSError, StopIteration, json.decoder.JSONDecodeError) as e:
                print(f"No {consts.abbrv}_form_values.json to read from, continuing with default values")

    def __melee_chars(self):
        consts.custom = False
        consts.melee = True
        self.__update_chars(consts.melee_chars)

    def __ultimate_chars(self):
        consts.custom = False
        consts.melee = False
        self.__update_chars(consts.ult_chars)

    def __custom_chars(self):
        consts.custom = True
        consts.melee = False
        chars = None
        try:
            with open(consts.custom_list_file, "r") as f:
                chars = [x.strip() for x in f.read().split(",")]
            self.__update_chars(chars)
        except Exception as e:
            with open(consts.custom_list_file, "a") as f:
                pass
            print("A custom list file as been created for you to modify, it can be found at " + consts.custom_list_file)

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

    def __sa_update(self, data):
        prefix = ""
        mtype = ""
        suffix = ""
        if consts.melee:
            try:
                self.__p1chars = self._p1char.value
                self.__p2chars = self._p2char.value
                p1char = " ".join(data['image1'].split(" ")[:-1])
                p2char = " ".join(data['image2'].split(" ")[:-1])
                if p1char not in self.__p1chars:
                    self.__p1chars.append(p1char)
                if p2char not in self.__p2chars:
                    self.__p2chars.append(p2char)
                self._p1char.load_form(dict(selected=self.__p1chars))
                self._p2char.load_form(dict(selected=self.__p2chars))
            except Exception as e:
                print(e)
        try:
            self._p1.value = data['player1']
            self._p2.value = data['player2']
        except Exception as e:
            print(e)
        try:
            for t in consts.match_types:
                if t.lower() in data['match'].lower():
                    mtype = t
                    prefix = ""
                    suffix = ""
                    if not data['match'].find(t):
                        sections = data['match'].split(t)
                        suffix = sections[1].strip()
                    else:
                        sections = data['match'].split(t)
                        prefix = sections[0].strip()
                        suffix = sections[1].strip()
            self._mtype.value = mtype
            self._mprefix.value = prefix
            self._msuffix.value = suffix
        except Exception as e:
            print(e)

    def __sc_update(self, data):
        mtype = ""
        suffix = ""
        prefix = ""
        if consts.melee:
            try:
                self.__p1chars = self._p1char.value
                self.__p2chars = self._p2char.value
                p1char = data['p1_char']
                p2char = data['p2_char']
                if p1char == "Doctor Mario":
                    p1char = "Dr. Mario"
                if p2char == "Doctor Mario":
                    p2char = "Dr. Mario"
                if p1char not in self.__p1chars:
                    self.__p1chars.append(p1char)
                if p2char not in self.__p2chars:
                    self.__p2chars.append(p2char)
                self._p1char.load_form(dict(selected=self.__p1chars))
                self._p2char.load_form(dict(selected=self.__p2chars))
            except Exception as e:
                print(e)
        try:
            self._p1.value = data['p1_name']
            self._p2.value = data['p2_name']
        except Exception as e:
            print(e)
        try:
            for t in consts.match_types:
                if t.lower() in data['event_round'].lower():
                    mtype = t
                    suffix = ""
                    sections = data['event_round'].split(t)
                    suffix = sections[1].strip()
                    prefix = data['event_bracket']
                elif t.lower() in data['event_bracket'].lower():
                    mtype = t
                    prefix = ""
                    suffix = ""
            self._mtype.value = mtype
            self._mprefix.value = prefix
            self._msuffix.value = suffix
        except Exception as e:
            print(e)
