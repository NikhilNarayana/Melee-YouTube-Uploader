#!/usr/bin/env python3

import sys

import PySide2.QtCore
from PySide2.QtWidgets import QApplication, QLabel

if __name__ == "__main__":
    app = QApplication([])
    label = QLabel("Test")
    label.show()
    sys.exit(app.exec_())
