#!/usr/bin/env python3

import json
import re
from time import sleep

import requests
import websocket
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from .obswebsocket import events, obsws


class SAWorker(QObject):
    sig = pyqtSignal(object)
    data = None

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.addr = f"ws://{self.host}:{self.port}"

    def startws(self):
        try:
            self.ws = websocket.WebSocketApp(self.addr, on_message=self.get_update)
            print("Hooking into Scoreboard Assistant...")
            self.ws.run_forever()
        except:
            print("Failed to hook into Scoreboard Assistant")

    def closews(self):
        self.ws.close()

    def get_update(self, message):
        data = json.loads(message)
        data.pop("time")
        if self.data != data:
            self.data = data
            self.send_update()

    @pyqtSlot()
    def send_update(self):
        self.sig.emit(self.data)


class OBSWorker(QObject):
    sig = pyqtSignal(bool)

    def __init__(self, host, port, password):
        super().__init__()
        self.host = host
        self.port = port
        self.password = password

    def startobs(self):
        try:
            self.obs = obsws(self.host, self.port, self.password)
            self.obs.register(self.recordingStart, events.RecordingStarted)
            self.obs.register(self.recordingStop, events.RecordingStopped)
            self.obs.connect()
            print("Hooked into OBS")
        except Exception as e:
            print(e)
            print("Failed to connect to OBS")

    def closeobs(self):
        self.obs.disconnect()

    @pyqtSlot()
    def recordingStart(self, data=None):
        self.sig.emit(True)

    @pyqtSlot()
    def recordingStop(self, data=None):
        self.sig.emit(False)


class SCWorker(QObject):
    sig = pyqtSignal(object)
    data = None

    def __init__(self, file):
        super().__init__()
        self.file = file
        self._run = True

    def stopsc(self):
        self._run = False

    def get_update(self):
        while self._run:
            with open(self.file) as f:
                ndata = json.load(f)
                if not self.data:
                    self.data = ndata
                    self.send_update()
            if self.data["timestamp"] != ndata["timestamp"]:
                self.data = ndata
                self.send_update()
            sleep(5)

    @pyqtSlot()
    def send_update(self):
        self.sig.emit(self.data)


class StreametaWorker(QObject):
    sig = pyqtSignal(object)
    data = None

    def __init__(self, addr):
        super().__init__()
        self.addr = addr
        self._run = True

    def stopsm(self):
        self._run = False

    def get_update(self):
        try:
            while self._run:
                resp = requests.get(self.addr).json()
                if resp != self.data:
                    self.data = resp
                    self.send_update()
                sleep(10)
        except Exception as e:
            print(e)

    @pyqtSlot()
    def send_update(self):
        self.sig.emit(self.data)


class PiioWorker(QObject):
    sig = pyqtSignal(object)
    data = None

    def __init__(self, host, port):
        super().__init__()
        self.addr = f"ws://{host}:{port}"

    def startws(self):
        try:
            print("Hooking into Piio...")
            self.ws = websocket.WebSocketApp(
                url=self.addr,
                on_message=self.get_update,
                on_error=self.on_error,
                on_open=self.on_open_ws,
            )
            self.ws.run_forever()
        except:
            print("Failed to hook into Piio")

    def on_open_ws(self, ws):
        print("piio connection open")
        self.ws.send('{"type":"subscribe","data":"scoreboard"}')

    def closews(self):
        self.ws.close()

    def on_error(self, ws, error):
        print(error)

    def get_update(self, ws, message):
        raw_data = json.loads(message)

        indexedTeams = {}
        for team in raw_data["data"]["dbEntries"]["team"]:
            indexedTeams[team["_id"]] = team

        data = {
            "round": raw_data["data"]["scoreboard"]["fields"]["round"]["value"],
        }

        try:
            for index, team in raw_data["data"]["scoreboard"]["teams"].items():
                names = []
                for player in team["players"]:
                    name = player["name"]
                    teams_no_regex = []

                    for team_id in player["team"]:
                        team = indexedTeams[team_id]

                        if team["regex"]:
                            name = re.sub(team["regex"], team["prefix"], name)
                        else:
                            teams_no_regex.append(team)

                    if teams_no_regex:
                        delimiter = teams_no_regex[-1]["delimiter"]
                        team_names = map(lambda t: t["prefix"], teams_no_regex)
                        whole_prefix = " ".join(team_names) + delimiter
                        name = whole_prefix + name

                    names.append(name)

                data[f"player{index}"] = " & ".join(names)

        except Exception as e:
            print(e)
            raise e

        self.data = data
        self.send_update()

    def stop(self):
        self.ws.close()

    @pyqtSlot()
    def send_update(self):
        self.sig.emit(self.data)


class WriteWorker(QObject):

    textWritten = pyqtSignal(str)

    @pyqtSlot(str)
    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass
