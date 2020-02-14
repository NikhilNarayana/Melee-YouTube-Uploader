#!/usr/bin/env python3

from . import consts

from pyforms_lite import BaseWidget
from pyforms_lite.controls import ControlButton, ControlList


class OptionsViewer(BaseWidget):
    def __init__(self, pos, options):
        super(OptionsViewer, self).__init__(f"Options #{pos}")
        self.pos = pos
        self.options = options
        self._oview = ControlList()
        self._oview.horizontal_headers = ["Key", "Value"]
        self.formset = ["_oview"]
        if pos or consts.stop_thread:
            self._deletebutton = ControlButton("Remove from Queue")
            self._deletebutton.value = self.__delete_job
            self.formset = ["_oview", "=", "_deletebutton"]
        self.__update_o_view()
        self._oview.data_changed_event = self.__update_data
    
    def __update_data(self, row, col, item):
        if col == 1:
            var_name = self._oview.get_value(0, row)
            if "char" in var_name:
                item = item.split("/")
            self.options.__dict__[var_name] = item
            self.parent._MeleeUploader__update_qview(self.pos, self.options)
            print(f"{var_name} in queue item {self.pos} was updated to {item}")

    def __delete_job(self):
        self._oview.readonly = True
        self.close()
        self.parent._MeleeUploader__delete_from_queue_view(self.pos)

    def __update_o_view(self):
        self._oview.clear()
        for key in self.options.__dict__.keys():
            value = self.options.__dict__[key]
            if "char" in key:
                value = "/".join(value)
            self._oview += (key, value)
        self._oview.resize_rows_contents()


class HistoryViewer(BaseWidget):
    def __init__(self, history):
        super(HistoryViewer, self).__init__("History")
        self._history = history
        self._qview = ControlList(select_entire_row=True)
        self._qview.cell_double_clicked_event = self.__load_row
        self._qview.readonly = True
        self._qview.horizontal_headers = ["Player 1", "Player 2", "Match Type"]

        for options in self._history:
            self._qview += (options[3], options[4], " ".join((options[11], options[2], options[10])))

    def __load_row(self, row, c):
        self.parent._MeleeUploader__load_form(self._history[row])
