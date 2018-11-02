#!/usr/bin/env python3

from pyforms_lite import BaseWidget
from pyforms_lite.controls import ControlButton, ControlList


class OptionsViewer(BaseWidget):
    def __init__(self, pos, options, running, history=False, mainprog=None):
        super(OptionsViewer, self).__init__(f"Options #{pos}")
        self.options = options
        self._oview = ControlList()
        self._oview.readonly = True
        if history:
            self._oview.horizontal_headers = ["Value"]
            self._mainprog = mainprog
            self._loadbutton = ControlButton("Load")
            self._loadbutton.value = self.__load_row
            self.formset = ["_oview", "=", "_loadbutton"]
            for val in options:
                self._oview += (val,)
        elif pos or not running:
            self._oview.horizontal_headers = ["Key", "Value"]
            self._ignorebutton = ControlButton("Toggle Ignore")
            self._ignorebutton.value = self.__ignore_job
            self.formset = ["_oview", "=", "_ignorebutton"]
            self.__update_o_view()

    def __ignore_job(self):
        self.options.ignore = False if self.options.ignore else True
        print(f"Ignore set to {self.options.ignore}")
        self.__update_o_view()

    def __update_o_view(self):
        self._oview.clear()
        for key in self.options.__dict__.keys():
            value = self.options.__dict__[key]
            if "char" in key:
                value = "/".join(value)
            self._oview += (key, value)
        self._oview.resize_rows_contents()

    def __load_row(self):
        self._mainprog._MeleeUploader__load_form(self.options)  # this has got to be jank


class HistoryViewer(BaseWidget):
    def __init__(self, history, running, mainprog):
        super(HistoryViewer, self).__init__("History")
        self._mainprog = mainprog
        self._history = history
        self._running = running
        self._qview = ControlList(select_entire_row=True)
        self._qview.cell_double_clicked_event = self.__show_o_view
        self._qview.readonly = True
        self._qview.horizontal_headers = ["Player 1", "Player 2", "Match Type"]

        for options in self._history:
            self._qview += (options[3], options[4], " ".join((options[11], options[2], options[10])))

    def __show_o_view(self, row, column):
        win = OptionsViewer(row, self._history[row], self._running, True, self._mainprog)
        win.parent = self
        win.show()
