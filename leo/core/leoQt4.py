#@+leo-ver=5-thin
#@+node:ekr.20210407010904.1: * @file leoQt4.py
"""Import wrapper for pyQt4"""
# pylint: disable=import-error, unused-import
from PyQt4 import Qt
from PyQt4 import QtCore
from PyQt4 import QtGui
assert Qt and QtCore and QtGui  # For pyflakes.
from PyQt4.QtCore import QString
from PyQt4.QtCore import QUrl
from PyQt4.QtCore import pyqtSignal as Signal
assert QString and QUrl and Signal  # For pyflakes.
QtConst = QtCore.Qt
QtWidgets = QtGui
printsupport = QtWidgets
qt_version = QtCore.QT_VERSION_STR
#@-leo