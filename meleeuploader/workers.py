#!/usr/bin/env python3

import json
import threading
from time import sleep

import websocket
from obswebsocket import obsws, events
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot


class SAWorker(QObject):
    sig = pyqtSignal(object)
    data = None

    def __init__(self, addr):
        super().__init__()
        self.addr = addr

    def startws(self):
        self.ws = websocket.WebSocketApp(self.addr, on_message=self.get_update)
        self.ws.run_forever()

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
    sig = pyqtSignal()

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port

    def startobs(self):
        self.obs = obsws(self.host, self.port)
        self.obs.register(self.submit, events.RecordingStopped)
        self.obs.connect()

    def closeobs(self):
        self.obs.disconnect()

    @pyqtSlot()
    def submit(self, data=None):
        self.sig.emit()


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
            if self.data['timestamp'] != ndata['timestamp']:
                self.data = ndata
                self.send_update()
            sleep(5)

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
