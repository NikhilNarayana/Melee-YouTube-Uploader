#!/usr/bin/env python3

import json
import threading

import websocket
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot


class SAWorker(QObject):
    sig = pyqtSignal(object)
    data = None

    def __init__(self, addr):
        super().__init__()
        self.addr = addr

    def startws(self):
        self.ws = websocket.WebSocketApp(self.addr, on_message=self.get_update)
        self.thr = threading.Thread(target=self.ws.run_forever)
        self.thr.daemon = True
        self.thr.start()

    def closews(self):
        self.ws.close()
        self.thr.join()

    def get_update(self, message):
        data = json.loads(message)
        data.pop("time")
        if self.data != data:
            self.data = data
            self.send_update()

    @pyqtSlot()
    def send_update(self):
        self.sig.emit(self.data)
