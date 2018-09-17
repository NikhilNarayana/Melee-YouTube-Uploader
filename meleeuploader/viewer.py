#!/usr/bin/env python3

from pyforms_lite import BaseWidget
from pyforms_lite.controls import ControlButton, ControlList


class OptionsViewer(BaseWidget):
	def __init__(self, pos, options):
		super(OptionsViewer, self).__init__(f"Options #{pos}")
		self.options = options
		self._oview = ControlList()
		self._oview.horizontal_headers = ["Key", "Value"]
		if pos:
			self._ignorebutton = ControlButton("Toggle Ignore")
			self._ignorebutton.value = self.__ignore_job
		self._oview.readonly = True
		for key in options.__dict__.keys():
			value = options.__dict__[key]
			if "char" in key:
				value = "/".join(value)
			self._oview += (key, value)
		self._oview.resize_rows_contents()
		if pos:
			self.formset = ["_oview", "=", "_ignorebutton"]

	def __ignore_job(self):
		self.options.ignore = False if self.options.ignore else True
		print(f"Ignore set to {self.options.ignore}")