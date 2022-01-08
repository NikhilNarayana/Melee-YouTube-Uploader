#!/usr/bin/env python3

import os
import sys
import json
import pickle
import shutil
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
from pyforms_lite.controls import ControlText, ControlFile, ControlLabel
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
            self.warning("You must input a host IP and port number")


class OBSHostPortInput(BaseWidget):
    def __init__(self):
        super(OBSHostPortInput, self).__init__("OBS Websocket")
        self._host = ControlText("OBS IP")
        self._port = ControlText("OBS Port")
        self._password = ControlText("OBS Password")
        self._host.value = "localhost"
        self._port.value = "4444"
        self._label = ControlLabel("When I stop recording I want the program to")
        self._sub = ControlButton("Submit")
        self._stop = ControlButton("Stop Updates")
        self.formset = ["_host", "_port", "_password", "_label", ("_sub", "_stop")]
        self._sub.value = self.__sub_action
        self._stop.value = self.__stop_action

    def __sub_action(self):
        if self._host.value and self._port.value:
            self.parent._MeleeUploader__hook_obs(
                self._host.value, self._port.value, self._password.value, False
            )
        else:
            self.warning("You must input a host IP and port number")

    def __stop_action(self):
        if self._host.value and self._port.value:
            self.parent._MeleeUploader__hook_obs(
                self._host.value, self._port.value, self._password.value, True
            )
        else:
            self.warning("You must input a host IP and port number")


class SCSetup(BaseWidget):
    def __init__(self, mappings={}):
        super(SCSetup, self).__init__("Stream Control")
        self._mappings = mappings
        self._file = ControlFile("File")

        self._label = ControlLabel("Uploader Inputs to streamcontrol.json mappings\n")
        self._p1 = ControlText("P1 Name")
        self._p2 = ControlText("P2 Name")
        self._p1_sponsor = ControlText("P1 Sponsor")
        self._p2_sponsor = ControlText("P2 Sponsor")
        self._p1_char = ControlText("P1 Character")
        self._p2_char = ControlText("P2 Character")
        self._mtype = ControlText("Match Type")
        self._mprefix = ControlText("Match Prefix")

        self._button = ControlButton("Submit")
        self.formset = [
            "_file",
            "_label",
            "_p1",
            "_p2",
            "_p1_sponsor",
            "_p2_sponsor",
            "_p1_char",
            "_p2_char",
            "_mtype",
            "_mprefix",
            (" ", "_button", " "),
        ]

        self._p1.value = self._mappings.get("p1_name", "")
        self._p2.value = self._mappings.get("p2_name", "")
        self._p1_sponsor.value = self._mappings.get("p1_sponsor", "")
        self._p2_sponsor.value = self._mappings.get("p2_sponsor", "")
        self._p1_char.value = self._mappings.get("p1_char", "")
        self._p2_char.value = self._mappings.get("p2_char", "")
        self._mtype.value = self._mappings.get("mtype", "")
        self._mprefix.value = self._mappings.get("mprefix", "")

        self._file.value = self._mappings.get("file", "")

        self._file.form.lineEdit.setPlaceholderText("Find your streamcontrol.json")

        self._button.value = self.__button_action

    def __button_action(self, data=None):
        if self._file.value:
            self._mappings["file"] = self._file.value
            self._mappings["p1_name"] = self._p1.value
            self._mappings["p2_name"] = self._p2.value
            self._mappings["p1_sponsor"] = self._p1_sponsor.value
            self._mappings["p2_sponsor"] = self._p2_sponsor.value
            self._mappings["p1_char"] = self._p1_char.value
            self._mappings["p2_char"] = self._p2_char.value
            self._mappings["mtype"] = self._mtype.value
            self._mappings["mprefix"] = self._mprefix.value
            with open(consts.sc_form_values_file, "w") as f:
                json.dump(self._mappings, f)
            self.parent._MeleeUploader__hook_sc(self._mappings)
        else:
            self.warning("You must select a file")


class SMurlInput(BaseWidget):
    def __init__(self, url=""):
        super(SMurlInput, self).__init__("Streameta")
        self._url = ControlText("URL")
        self._url.value = url.value
        self._url.form.lineEdit.setPlaceholderText(
            "http://ns.streameta.com/api/?token=<token>"
        )

        self._button = ControlButton("Submit")
        self._button.value = self.__button_action

    def __button_action(self, data=None):
        if self._url.value:
            self.parent._MeleeUploader__hook_sm(self._url.value)
        else:
            self.warning("You must provide a URL")


class YouTubeSelector(BaseWidget):
    def __init__(self):
        super(YouTubeSelector, self).__init__("YouTubeSelector")
        self._youtubes = ControlCombo("Accounts")
        self._ok = ControlButton("Load")
        self._new = ControlButton("New Account")

        self.formset = ["_youtubes", ("_ok", "_new")]

        accounts = os.listdir(consts.yt_accounts_folder)
        for account in accounts:
            self._youtubes += (account.split(".")[0], account)

        self._ok.value = self._ok_action
        self._new.value = self._new_action

    def _ok_action(self):
        account = self._youtubes.value
        shutil.copyfile(
            os.path.join(consts.yt_accounts_folder, account), consts.youtube_oauth_file
        )
        QtCore.QCoreApplication.instance().quit()

    def _new_action(self):
        QtCore.QCoreApplication.instance().quit()


class MeleeUploader(BaseWidget):
    def __init__(self):
        try:  # check if the user can update the app
            latest_version = (
                requests.get("https://pypi.org/pypi/MeleeUploader/json")
                .json()
                .get("info", {})
                .get("version")
            )
            if sv(latest_version) > sv(
                consts.__version__
            ):  # prevents messages when developing
                if "linux" in sys.platform:
                    self.info(
                        f"Current Version: {consts.__version__}\nVersion {latest_version} is available.\nUse sudo pip3 install -U meleeuploader=={latest_version} in terminal to update to the newest verison",
                        title="MeleeUploader",
                    )
                else:
                    resp = self.question(
                        f"Current Version: {consts.__version__}\nVersion {latest_version} is available. Would you like to update?",
                        title="MeleeUploader",
                    )
                    if resp == "yes":
                        ret = subprocess.call(
                            (
                                "pip3",
                                "install",
                                "-U",
                                f"meleeuploader=={latest_version}",
                            )
                        )
                        if ret:
                            self.info(
                                f'The app failed to update\nType "pip3 install -U meleeuploader=={latest_version}" into CMD/Terminal to update',
                                title="MeleeUploader",
                            )
                        else:
                            self.info(
                                "You can now restart the app to use the new version",
                                title="MeleeUploader",
                            )
        except Exception as e:
            print(e)

        super(MeleeUploader, self).__init__(
            f"Melee YouTube Uploader - {consts.__version__}"
        )

        # Redirct print output
        sys.stdout = workers.WriteWorker(textWritten=self.write_print)

        # Websocket
        self._sa = None
        self._obs = None

        # History
        self.__history = []

        # Queue
        self._queue = Queue()
        self._queueref = (
            []
        )  # out of order access to all the items in _queue with mutation
        consts.start_queue = True if "-q" in sys.argv else False

        # Event Values
        self._privacy = ControlCombo("Video Privacy")
        self._title_format = ControlCombo("Title Format")
        self._ename = ControlText("Event Name")
        self._ename_min = ControlText()
        self._pID = ControlText("Playlist ID")
        self._bracket = ControlText("Bracket Link")
        self._tags = ControlText("Tags")
        self._description = ControlTextArea("Description")
        self._timestamp_start = None
        self._timestamps = []

        # Match Values
        self._file = ControlFile("File")
        self._p1 = ControlText()
        self._p2 = ControlText()
        self._p1_sponsor = ControlText("P1")
        self._p2_sponsor = ControlText("P2")
        self._p1char = ControlCheckBoxList("P1 Characters")
        self._p2char = ControlCheckBoxList("P2 Characters")
        self._mtype = ControlCombo()
        self._mprefix = ControlText()
        self._msuffix = ControlText()

        # Output Box
        self._output = ControlTextArea()
        self._output.readonly = True
        self._qview = ControlList("Queue", select_entire_row=True)
        self._qview.cell_double_clicked_event = self.__show_oview
        self._qview.readonly = True
        self._qview.horizontal_headers = ["Player 1", "Player 2", "Round"]

        # Button
        self._submit_button = ControlButton("Submit")
        self._submit_button.value = self.__on_submit

        self._timestamp_button = ControlButton("Record Timestamp")
        self._timestamp_button.value = self.__on_timestamp

        # Title Formats
        for f in consts.title_format:
            self._title_format += f

        # Form Layout
        self.formset = [
            {
                "-Match": [
                    "_file",
                    (" ", "_mprefix", "_mtype", "_msuffix", " "),
                    (" ", "_p1_sponsor", "_p1", " "),
                    (" ", "_p1char", " "),
                    (" ", "_p2_sponsor", "_p2", " "),
                    (" ", "_p2char", " "),
                    (" ", "_timestamp_button", " "),
                ],
                "-Status-": ["_output", "=", "_qview"],
                "Event-": [
                    "_privacy",
                    "_title_format",
                    ("_ename", "_ename_min"),
                    "_pID",
                    "_bracket",
                    "_tags",
                    "_description",
                ],
            },
            (" ", "_submit_button", " "),
        ]

        # Main Menu Layout
        self.mainmenu = [
            {
                "Settings": [
                    {"YouTube Log Out": self.__reset_yt_cred},
                    {"Toggle OBS Hook": self.__show_obs_form},
                    {"Toggle SA Hook": self.__show_sa_form},
                    {"Toggle SC Hook": self.__show_sc_form},
                    {"Toggle Streameta Hook": self.__show_sm_form},
                    {"About": self.__about_info},
                ],
                "Save/Clear": [
                    {"Save Form": self.__save_form},
                    {"Clear Match Values": self.__reset_match},
                    {"Clear Event Values": self.__reset_event},
                    {"Clear All": self.__reset_forms},
                ],
                "Queue": [
                    {"Toggle Uploads": utils.toggle_worker},
                    {"Save Queue": self.__save_queue},
                    {"Load Queue": self.__load_queue},
                    {"Toggle Save on Submit": self.__save_on_submit},
                ],
                "History": [{"Show History": self.__show_hview}],
                "Characters": [
                    {"Melee": self.__melee_chars},
                    {"Ultimate": self.__ultimate_chars},
                    {"64": self.__64_chars},
                    {"Rivals": self.__rivals_chars},
                    {"Splatoon": self.__splatoon_chars},
                    {"Strive": self.__strive_chars},
                    {"NASB": self.__nasb_chars},
                    {"Custom": self.__custom_chars},
                ],
            }
        ]

        # Add ControlCombo values
        for t in consts.match_types:
            self._mtype += t
        for t in ("unlisted", "public", "private"):
            self._privacy += t

        # Set placeholder text
        self._ename_min.form.lineEdit.setPlaceholderText("Shortened Event Name")
        self._p1_sponsor.form.lineEdit.setPlaceholderText("Sponsor Tag")
        self._p2_sponsor.form.lineEdit.setPlaceholderText("Sponsor Tag")
        self._p1.form.lineEdit.setPlaceholderText("P1 Name")
        self._p2.form.lineEdit.setPlaceholderText("P2 Name")
        self._mprefix.form.lineEdit.setPlaceholderText("Round Prefix")
        self._msuffix.form.lineEdit.setPlaceholderText("Round Suffix")
        self._bracket.form.lineEdit.setPlaceholderText("Include https://")
        self._tags.form.lineEdit.setPlaceholderText("Separate with commas")
        self._pID.form.lineEdit.setPlaceholderText(
            "Accepts full YT link or a new playlist title"
        )

        # For pulling characters
        self.__p1chars = []
        self.__p2chars = []

        # Set character list
        self.game_chars = {
            "64": self.__64_chars,
            "melee": self.__melee_chars,
            "ult": self.__ultimate_chars,
            "rivals": self.__rivals_chars,
            "splatoon": self.__splatoon_chars,
            "strive": self.__strive_chars,
            "custom": self.__custom_chars,
        }
        self.game_chars[consts.game]()

        # Stream Control
        self._sc = None
        self.__sc_mapping = {  # defaults are based on Recursion's setup
            "file": "",
            "p1_name": "p1_name",
            "p2_name": "p2_name",
            "p1_char": "p1_char",
            "p2_char": "p2_char",
            "p1_sponsor": "p1_sponsor",
            "p2_sponsor": "p2_sponsor",
            "mtype": "event_round",
            "mprefix": "event_bracket",
        }

        # Streameta
        self._sm = None
        self._smf = ControlText()
        self._smf.value = ""

        # Define the mapping of the form values json to form fields
        self._form_fields = {
            "ename": self._ename,
            "pID": self._pID,
            "mtype": self._mtype,
            "p1": self._p1,
            "p2": self._p2,
            "p1char": self._p1char,
            "p2char": self._p2char,
            "bracket": self._bracket,
            "file": self._file,
            "tags": self._tags,
            "msuffix": self._msuffix,
            "mprefix": self._mprefix,
            "p1sponsor": self._p1_sponsor,
            "p2sponsor": self._p2_sponsor,
            "privacy": self._privacy,
            "description": self._description,
            "ename_min": self._ename_min,
            "title_format": self._title_format,
            "streameta_url": self._smf,
        }

        # Get latest values from form_values.txt
        if consts.start_queue:
            self.__load_queue()
        else:
            self.__load_form()

    def __on_submit(self, data=None):
        """Button action event"""
        consts.submitted = True
        if any(
            not x
            for x in (
                self._ename.value,
                self._p1.value,
                self._p2.value,
                self._file.value,
            )
        ):
            print(
                "Missing one of the required fields (event name, player names, file name)"
            )
            return
        self.__p1chars = []
        self.__p2chars = []
        options = Namespace()
        self.__history.append(self.__save_form())
        options.ename = self._ename.value
        options.ename_min = self._ename_min.value or options.ename
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
            options.file = max(
                [
                    os.path.join(self._file.value, f)
                    for f in os.listdir(self._file.value)
                    if os.path.isfile(os.path.join(self._file.value, f))
                ],
                key=os.path.getmtime,
            )
        else:
            options.file = self._file.value
        options.tags = self._tags.value
        options.msuffix = self._msuffix.value
        options.mprefix = self._mprefix.value
        options.privacy = self._privacy.value
        options.descrip = self._description.value
        options.timestamps = "\n".join(self._timestamps)
        self._timestamps = []
        options.title_format = self._title_format.value
        if self._p1_sponsor.value:
            options.p1 = " | ".join((self._p1_sponsor.value, options.p1))
        if self._p2_sponsor.value:
            options.p2 = " | ".join((self._p2_sponsor.value, options.p2))
        options.ignore = False
        self.__reset_match(False, isadir)
        self.__add_to_qview(options)
        self._queueref.append(options)
        if consts.first_run:
            thr = threading.Thread(target=self.__worker)
            thr.daemon = True
            thr.start()
            consts.first_run = False
        if consts.save_on_submit:
            self.__save_queue(True)

    def __on_timestamp(self):
        if self._timestamp_start is None:
            print("Timestamp is not recorded because OBS is not recording")
            return

        if len(self._timestamps) == 0:
            self._timestamps.append("Timestamps:")
            self._timestamps.append("0:00:00 - Intro")
        tdelta = str(datetime.now() - self._timestamp_start).split(".")[0]
        timestamp_format = consts.timestamp_format[self._title_format.value]
        if all(x for x in [self._p1char.value, self._p2char.value]):
            timestamp_info = timestamp_format.format(
                p1=self._p1.value,
                p2=self._p2.value,
                p1char="/".join(self._p1char.value),
                p2char="/".join(self._p2char.value),
            )
            self._timestamps.append(f"{tdelta} - {timestamp_info}")
            return

        self._timestamps.append(f"{tdelta} - {self._p1.value} vs {self._p2.value}")

    def write_print(self, text):
        self._output.value += text
        self._output._form.plainTextEdit.moveCursor(QtGui.QTextCursor.End)
        if sys.__stdout__:
            print(text, file=sys.__stdout__, end="")

    def write_err(self, text):
        if sys.__stdout__:
            print(text, file=sys.__stdout__, end="")
        with open(consts.log_file, "a") as f:
            f.write(text)

    def __reset_yt_cred(self):
        channel_name = (
            consts.youtube.channels()
            .list(part="snippet", mine=True)
            .execute()
            .get("items", [])[0]
            .get("snippet", {})
            .get("title")
        )
        resp = self.question(
            f"You are currently logged into {channel_name}\nWould you like to log out?",
            title="MeleeUploader",
        )
        if resp == "yes":
            shutil.copyfile(
                consts.youtube_oauth_file,
                os.path.join(consts.yt_accounts_folder, f"{channel_name}.json"),
            )
            if consts.youtube:
                os.remove(consts.youtube_oauth_file)
            sys.exit(0)

    def __reset_match(self, menu=True, isadir=False):
        self._p1char.load_form(dict(selected=[]))
        self._p2char.load_form(dict(selected=[]))
        self._p1.value = ""
        self._p2.value = ""
        self._p1_sponsor.value = ""
        self._p2_sponsor.value = ""
        self._msuffix.value = ""
        if menu:
            isadir = os.path.isdir(self._file.value)
            if not isadir:
                self._file.value = ""
            self._mtype.value = "Pools"
            self._mprefix.value = ""
        elif not isadir:
            self._file.value = ""

    def __reset_event(self):
        self._privacy.value = "public"
        self._title_format.value = (
            "{ename} - {round} - {p1} ({p1char}) vs {p2} ({p2char})"
        )
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
                    data = {"game": deepcopy(consts.game)}
                    data["ename"] = deepcopy(options.ename)
                    data["pID"] = deepcopy(options.pID)
                    data["bracket"] = deepcopy(options.bracket)
                    data["tags"] = deepcopy(options.tags)
                    data["mprefix"] = deepcopy(options.mprefix)
                    data["privacy"] = deepcopy(options.privacy)
                    data["description"] = deepcopy(options.descrip)
                    data["ename_min"] = deepcopy(options.ename_min)
                    data["title_format"] = deepcopy(options.title_format)
                    with open(consts.form_values_file, "w") as f:
                        json.dump(data, f)
                    if consts.save_on_submit:
                        self.__save_queue(True)
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
            return

        self._sawin = SAHostPortInput()
        self._sawin.parent = self
        self._sawin.show()

    def __show_obs_form(self):
        if self._obs:
            self._obs.closeobs()
            print("Unhooked from OBS")
            self._obst.quit()
            self._obs = None
            return

        self._obswin = OBSHostPortInput()
        self._obswin.parent = self
        self._obswin.show()

    def __show_sc_form(self):
        if self._sc:
            self._sc.stopsc()
            print("Unhooked from SC")
            self._sct.quit()
            self._sc = None
            return

        try:
            with open(consts.sc_form_values_file, "r") as f:
                self.__sc_mapping = json.load(f)
        except Exception:
            pass
        self._scwin = SCSetup(self.__sc_mapping)
        self._scwin.parent = self
        self._scwin.show()

    def __show_sm_form(self):
        if self._sm:
            self._sm.stopsm()
            print("Unhooked from Streameta")
            self._smt.quit()
            self._sm = None
            return

        self._smwin = SMurlInput(self._smf)
        self._smwin.parent = self
        self._smwin.show()

    def __hook_sa(self, host, port):
        self._sawin.close()
        self.warning(
            "Please make sure Scoreboard Assistant is open", title="MeleeUploader"
        )
        self._sa = workers.SAWorker(host, port)
        self._sat = QtCore.QThread()
        self._sa.moveToThread(self._sat)
        self._sa.sig.connect(self.__sa_update)
        self._sat.started.connect(self._sa.startws)
        self._sat.start()

    def __hook_obs(self, host, port, password, stopUpdates):
        consts.stop_updates = stopUpdates
        self._obswin.close()
        self.warning(
            "Please make sure OBS is open and the Websocket server is enabled",
            title="MeleeUploader",
        )
        self._obs = workers.OBSWorker(host, port, password)
        self._obst = QtCore.QThread()
        self._obs.moveToThread(self._obst)
        self._obs.sig.connect(self.__handle_obs)
        self._obst.started.connect(self._obs.startobs)
        self._obst.start()

    def __handle_obs(self, recording):
        if recording:
            # timestamps for the description will use this as 00:00
            self._timestamp_start = datetime.now()
            return

        self._timestamp_start = None
        if consts.stop_updates:
            consts.submitted = False
            return
        self.__on_submit()

    def __hook_sc(self, mappings):
        self.__sc_mapping = mappings
        self._scwin.close()
        self._sc = workers.SCWorker(mappings.get("file", ""))
        self._sct = QtCore.QThread()
        self._sc.moveToThread(self._sct)
        self._sc.sig.connect(self.__sc_update)
        self._sct.started.connect(self._sc.get_update)
        self._sct.start()
        print("Hooked into SC")

    def __hook_sm(self, url):
        try:
            self._smwin.close()
            self._smf.value = url
            self._sm = workers.StreametaWorker(url)
            self._smt = QtCore.QThread()
            self._sm.moveToThread(self._smt)
            self._sm.sig.connect(self.__sm_update)
            self._smt.started.connect(self._sm.get_update)
            self._smt.start()
            print("Hooked into Streameta")
        except Exception as e:
            print(e)

    def __show_oview(self, row, column):
        win = OptionsViewer(row, self._queueref[row])
        win.parent = self
        win.show()

    def __show_hview(self):
        self._hwin = HistoryViewer(self.__history)
        self._hwin.parent = self
        self._hwin.show()

    def __add_to_qview(self, options):
        self._qview += (
            options.p1,
            options.p2,
            " ".join((options.mprefix, options.mmid, options.msuffix)),
        )
        self._queue.put(options)
        self._qview.resize_rows_contents()

    def __update_qview(self, row, options):
        self._qview.set_value(0, row, options.p1)
        self._qview.set_value(1, row, options.p2)
        self._qview.set_value(
            2, row, " ".join((options.mprefix, options.mmid, options.msuffix))
        )
        self._qview.resize_rows_contents()

    def __delete_from_queue_view(self, job_num):
        job = self._queueref.pop(job_num)
        job.ignore = True
        self._qview -= job_num

    def __save_queue(self, silent=False):
        if os.path.exists(consts.queue_values_file) and not silent:
            resp = self.question(
                f"A queue already exists would you like to overwrite it?\nIt was last modified on {datetime.utcfromtimestamp(int(os.path.getmtime(consts.queue_values_file))).strftime('%Y-%m-%d')}"
            )
            if resp == "yes":
                with open(consts.queue_values_file, "wb") as f:
                    pickle.dump(self._queueref, f)
                print("Saved Queue, you can now close the program")
            elif resp == "no":
                resp = self.question(
                    "Would you like to add onto the end of that queue?"
                )
                if resp == "yes":
                    queueref = None
                    with open(consts.queue_values_file, "rb") as f:
                        queueref = pickle.load(f)
                    queueref.extend(self._queueref)
                    with open(consts.queue_values_file, "wb") as f:
                        pickle.dump(queueref, f)
                    print("Saved Queue, you can now close the program")
                else:
                    self.alert("Not saving queue", title="MeleeUploader")
            return

        with open(consts.queue_values_file, "wb") as f:
            pickle.dump(self._queueref, f)
            print("Saved Queue, you can now close the program")

    def __load_queue(self):
        if self._queueref and not consts.start_queue:
            resp = self.question(
                "Would you like to add to the existing queue?\nItems will be added to the front of the queue."
            )
            if resp == "yes":
                try:
                    with open(consts.queue_values_file, "rb") as f:
                        queueref = pickle.load(f)
                    queueref.extend(self._queueref)
                    self._queueref = queueref
                    self._qview.clear()
                    self._qview.horizontal_headers = ["Player 1", "Player 2", "Round"]
                    for options in self._queueref:
                        self.__add_to_qview(options)
                        self.__history.append(self.__save_form(options))
                except Exception:
                    print("You need to save a queue before loading a queue")
                    return
        else:
            try:
                with open(consts.queue_values_file, "rb") as f:
                    self._queueref = pickle.load(f)
                for options in self._queueref:
                    self.__add_to_qview(options)
                    self.__history.append(self.__save_form(options))
            except Exception as e:
                print("You need to save a queue before loading a queue")
                print(e)
                return
        if not consts.start_queue:
            resp = self.question(
                "Do you want to start uploading?", title="MeleeUploader"
            )
            if resp == "yes":
                thr = threading.Thread(target=self.__worker)
                thr.daemon = True
                consts.first_run = False
                consts.stop_thread = False
                thr.start()
            else:
                consts.stop_thread = True
            consts.loaded_queue = True
        else:
            thr = threading.Thread(target=self.__worker)
            thr.daemon = True
            consts.first_run = False
            consts.stop_thread = False
            thr.start()
            consts.loaded_queue = True

    def __save_on_submit(self):
        consts.save_on_submit = not consts.save_on_submit
        print(
            f"Save Queue on Submit is turned {'on' if consts.save_on_submit else 'off'}."
        )

    def __save_form(self, options=[]):
        data = {"game": deepcopy(consts.game)}
        if options:
            f = options.pID.find("PL")
            if f == -1 and options.pID:
                options.pID = utils.create_playlist(options.pID)
            else:
                options.pID = options.pID[f : f + 34]
            data["ename"] = deepcopy(options.ename)
            data["pID"] = deepcopy(options.pID)
            data["mtype"] = deepcopy(options.mtype)
            data["p1"] = deepcopy(options.p1)
            data["p2"] = deepcopy(options.p2)
            data["p1char"] = deepcopy(options.p1char)
            data["p2char"] = deepcopy(options.p2char)
            data["bracket"] = deepcopy(options.bracket)
            data["file"] = deepcopy(options.file)
            data["tags"] = deepcopy(options.tags)
            data["msuffix"] = deepcopy(options.msuffix)
            data["mprefix"] = deepcopy(options.mprefix)
            data["privacy"] = deepcopy(options.privacy)
            data["description"] = deepcopy(options.descrip)
            data["ename_min"] = deepcopy(options.ename_min)
            data["title_format"] = deepcopy(options.title_format)
            data["streameta_url"] = deepcopy(self._smf.value)
        else:
            f = self._pID.value.find("PL")
            if f == -1 and self._pID.value:
                self._pID.value = utils.create_playlist(self._pID.value)
            else:
                self._pID.value = self._pID.value[f : f + 34]
            for key, form in self._form_fields.items():
                data[key] = deepcopy(form.value)
        with open(consts.form_values_file, "w") as f:
            json.dump(data, f)
        return data

    def __load_form(self, values=[]):
        if values:
            self._hwin.close()
            for key, form in self._form_fields.items():
                value = values.get(key, None)
                if isinstance(value, (list, dict)):
                    form.load_form(dict(selected=value))
                elif value is not None:
                    form.value = value
            return
        try:
            with open(consts.form_values_file, "r") as f:
                values = json.loads(f.read())
                saved_game = values.get("game", "")
                if saved_game != consts.game and any(
                    saved_game == game for game in self.game_chars.keys()
                ):
                    ret = self.question(
                        f"Last game used was {saved_game}, would you like to switch to it?"
                    )
                    if ret == "yes":
                        self.game_chars[saved_game]()
                for key, form in self._form_fields.items():
                    value = values.get(key, None)
                    if isinstance(value, (list, dict)):
                        form.load_form(dict(selected=value))
                    elif value is not None:
                        form.value = value
        except (IOError, OSError, StopIteration, json.decoder.JSONDecodeError):
            print(
                f"No {os.path.basename(consts.form_values_file)} to read from, continuing with default values"
            )

    def __melee_chars(self):
        consts.game = "melee"
        consts.tags = consts.melee_tags
        self.__update_chars(consts.melee_chars)

    def __ultimate_chars(self):
        consts.game = "ultimate"
        consts.tags = consts.ult_tags
        self.__update_chars(consts.ult_chars)

    def __64_chars(self):
        consts.game = "64"
        consts.tags = consts.s64_tags
        self.__update_chars(consts.s64_chars)

    def __rivals_chars(self):
        consts.game = "rivals"
        consts.tags = consts.rivals_tags
        self.__update_chars(consts.rivals_chars)

    def __splatoon_chars(self):
        consts.game = "splatoon"
        consts.tags = consts.splatoon2_tags
        self.__update_chars(consts.splat_chars)

    def __strive_chars(self):
        consts.game = "strive"
        consts.tags = consts.strive_tags
        self.__update_chars(consts.strive_chars)

    def __nasb_chars(self):
        consts.game = "nasb"
        consts.tags = consts.nasb_tags
        self.__update_chars(consts.nasb_chars)

    def __custom_chars(self):
        chars = []
        try:
            with open(consts.custom_list_file, "r") as f:
                if os.path.getsize(consts.custom_list_file) > 0:
                    chars = [x.strip() for x in f.read().split(",")]
            self.__update_chars(chars)
            consts.game = "custom"
            consts.tags = ""
        except Exception:
            with open(consts.custom_list_file, "a") as f:
                pass
            print(
                f"A custom list file as been created for you to modify, it can be found at {consts.custom_list_file}"
            )
            self.alert(
                f"A custom list file as been created for you to modify, it can be found at {consts.custom_list_file}",
                title="MeleeUploader",
            )

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
        if consts.stop_updates and not consts.submitted:
            return
        prefix = ""
        mtype = ""
        suffix = ""
        try:
            self.__p1chars = self._p1char.value
            self.__p2chars = self._p2char.value
            p1char = " ".join(data.get("image1", "").split(" ")[:-1])
            p2char = " ".join(data.get("image2", "").split(" ")[:-1])
            if p1char not in self.__p1chars:
                self.__p1chars.append(p1char)
            if p2char not in self.__p2chars:
                self.__p2chars.append(p2char)
            self._p1char.load_form(dict(selected=self.__p1chars))
            self._p2char.load_form(dict(selected=self.__p2chars))
        except Exception as e:
            print(e)
        self._p1.value = data.get("player1", self._p1.value)
        self._p2.value = data.get("player2", self._p2.value)
        try:
            match = data.get("match", None)
            if match:
                for t in consts.match_types:
                    if t.lower() in match.lower():
                        mtype = t
                        prefix = ""
                        suffix = ""
                        if not match.find(t):
                            sections = match.split(t)
                            suffix = sections[1].strip()
                        if match.find(t) == -1 and match.find(t.lower()) >= 0:
                            pass
                        else:
                            sections = match.split(t)
                            prefix = sections[0].strip()
                            suffix = sections[1].strip()
                self._mtype.value = mtype
                self._mprefix.value = prefix
                self._msuffix.value = suffix
        except Exception as e:
            print(e)

    def __sc_update(self, data):
        if consts.stop_updates and not consts.submitted:
            return
        mtype = ""
        suffix = ""
        prefix = ""
        try:
            self.__p1chars = self._p1char.value
            self.__p2chars = self._p2char.value
            sc_p1_char = data.get(self.__sc_mapping["p1_char"], "")
            sc_p2_char = data.get(self.__sc_mapping["p2_char"], "")
            p1char = consts.sc_map_chars.get(sc_p1_char, sc_p1_char)
            p2char = consts.sc_map_chars.get(sc_p2_char, sc_p2_char)
            if p1char not in self.__p1chars:
                self.__p1chars.append(p1char)
            if p2char not in self.__p2chars:
                self.__p2chars.append(p2char)
            self._p1char.load_form(dict(selected=self.__p1chars))
            self._p2char.load_form(dict(selected=self.__p2chars))
        except Exception as e:
            print(e)
        try:
            self._p1.value = data.get(self.__sc_mapping["p1_name"], self._p1.value)
            self._p2.value = data.get(self.__sc_mapping["p2_name"], self._p2.value)
        except Exception as e:
            print(e)
        try:
            self._p1_sponsor.value = data.get(
                self.__sc_mapping["p1_sponsor"], self._p1_sponsor.value
            )
            self._p2_sponsor.value = data.get(
                self.__sc_mapping["p2_sponsor"], self._p2_sponsor.value
            )
        except Exception as e:
            print(e)
        try:
            match = data.get(self.__sc_mapping["mtype"], "")
            if match:
                for t in consts.match_types:
                    if t.lower() in match.lower() and match.find(t) != -1:
                        mtype = t
                        suffix = ""
                        sections = match.split(t)
                        suffix = sections[1].strip()
                        prefix = data.get(self.__sc_mapping["mprefix"], "")
                    elif (
                        t.lower() in data.get(self.__sc_mapping["mprefix"], "").lower()
                        and data.get(self.__sc_mapping["mprefix"], "").find(t) != -1
                    ):
                        mtype = t
                        prefix = ""
                        suffix = ""
                self._mtype.value = mtype
                self._mprefix.value = prefix
                self._msuffix.value = suffix
        except Exception as e:
            print(e)

    def __sm_update(self, data):
        if consts.stop_updates and not consts.submitted:
            return
        mtype = ""
        suffix = ""
        prefix = ""
        try:
            self.__p1chars = self._p1char.value
            self.__p2chars = self._p2char.value
            p1char = (
                data.get("teams", [])[0]
                .get("players", [])[0]
                .get("character", {})
                .get("name")
            )
            p2char = (
                data.get("teams", [])[1]
                .get("players", [])[0]
                .get("character", {})
                .get("name")
            )
            if p1char not in self.__p1chars:
                self.__p1chars.append(p1char)
            if p2char not in self.__p2chars:
                self.__p2chars.append(p2char)
            self._p1char.load_form(dict(selected=self.__p1chars))
            self._p2char.load_form(dict(selected=self.__p2chars))
        except Exception as e:
            print(e)
        try:
            self._p1.value = (
                data.get("teams", [])[0]
                .get("players", [])[0]
                .get("person", {})
                .get("name", self._p1.value)
            )
            self._p2.value = (
                data.get("teams", [])[1]
                .get("players", [])[0]
                .get("person", {})
                .get("name", self._p2.value)
            )
        except Exception as e:
            print(e)
        try:
            match = data.get("rounds", [])[0].get("round", {}).get("name", "")
            if match:
                for t in consts.match_types:
                    if t.lower() in match.lower() and match.find(t) != -1:
                        mtype = t
                        sections = match.split(t)
                        prefix = sections[0].strip()
                        suffix = sections[1].strip()
                self._mtype.value = mtype
                self._mprefix.value = prefix
                self._msuffix.value = suffix
        except Exception as e:
            print(e)

    def __about_info(self):
        self.info(
            f"v{consts.__version__}\nWritten by Nikhil Narayana\nhttps://github.com/NikhilNarayana/Melee-YouTube-Uploader"
        )
