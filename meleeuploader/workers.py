#!/usr/bin/env python3

import json

from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot


class SAWorker(QObject):
    sig = pyqtSignal(object)
    data = None

    def __init__(self, addr):
        super().__init__()
        self.ws = websocket.WebSocketApp(addr, on_message=self.get_update)
        self.ws.run_forever()

    def closews(self):
        self.ws.close()
    
    def get_update(self, message):
        data = json.loads(message)
        if self.data != data:
            self.data = data
            self.send_update()

    @pyqtSlot()
    def send_update(self):
        self.sig.emit(self.data)
