#!/usr/bin/env python3

from pyforms_lite import BaseWidget
from pyforms_lite.controls import ControlButton, ControlList


class OptionsViewer(BaseWidget):
	def __init__(self, pos, options, running):
		super(OptionsViewer, self).__init__(f"Options #{pos}")
		self.options = options
		self._oview = ControlList()
		self._oview.horizontal_headers = ["Key", "Value"]
		if pos or not running:
			self._ignorebutton = ControlButton("Toggle Ignore")
			self._ignorebutton.value = self.__ignore_job
			self.formset = ["_oview", "=", "_ignorebutton"]
		self._oview.readonly = True
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
