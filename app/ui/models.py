# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Dmitriy Yefremov
#
# This file is part of E2Toolkit.
#
# E2Toolkit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# E2Toolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with E2Toolkit.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Dmitriy Yefremov
#

__all__ = ["ServicesModel", "FavModel", "BouquetsModel", "SatelliteModel", "SatelliteTransponderModel",
           "PiconModel", "EpgModel", "TimerModel", "FtpModel", "FileModel", "ServiceTypeModel"]

from PyQt5 import QtGui, QtWidgets, QtCore

from app.ui.uicommons import Column


class ServicesModel(QtCore.QSortFilterProxyModel):
    HEADER_LABELS = ("", "", "", "Picon", "", "Name", "", "", "Package", "Type",
                     "SID", "Frec", "SR", "Pol", "FEC", "System", "Pos", "", "", "")

    CENTERED_COLUMNS = {Column.TYPE, Column.SSID, Column.RATE, Column.FREQ,
                        Column.POL, Column.FEC, Column.SYSTEM, Column.POS}

    FILTER_COLUMNS = (Column.NAME, Column.PACKAGE, Column.TYPE, Column.POS)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = QtGui.QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(self.HEADER_LABELS)
        self.setSourceModel(self.model)
        self._picon_path = ""
        self._filter_text = ""
        # Filter delay timer
        self.filter_timer = QtCore.QTimer(self)
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.filter)

    def data(self, index, role):
        column = index.column()
        if role == QtCore.Qt.DecorationRole and column == Column.PICON:
            return QtGui.QIcon(self._picon_path + self.index(index.row(), Column.PICON_ID).data())
        elif role == QtCore.Qt.TextAlignmentRole and column in self.CENTERED_COLUMNS:
            return QtCore.Qt.AlignCenter
        return super().data(index, role)

    def appendRow(self, *__args):
        self.model.appendRow(*__args)

    @property
    def picon_path(self):
        return self._picon_path

    @picon_path.setter
    def picon_path(self, value):
        self._picon_path = value

    def set_filter_text(self, text):
        """ Sets text for filter and starts delay timer. """
        self._filter_text = text
        self.filter_timer.start(500)

    def filter(self):
        """ Filter by the specified text in the main visible columns [NAME, PACKAGE, etc.]. """
        reg = QtCore.QRegExp(self._filter_text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.RegExp)
        self.setFilterRegExp(reg)
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        regex = self.filterRegExp()
        if regex.isEmpty():
            return True

        ans = (regex.indexIn(self.model.index(source_row, c, source_parent).data()) != -1 for c in self.FILTER_COLUMNS)
        return any(ans)


class FavModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("", "", "", "Picon", "", "Name", "", "", "", "Type", "", "", "", "", "", "", "Pos", "", "", "")
    CENTERED_COLUMNS = {Column.TYPE, Column.POS}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS)
        self._picon_path = ""

    def dropMimeData(self, data, action, row, column, parent):
        """ Overridden to prevent data being dragged into a cell. Column -> 0. """
        return super().dropMimeData(data, action, row, 0, parent)

    def data(self, index, role):
        column = index.column()
        if role == QtCore.Qt.DecorationRole and column == Column.PICON:
            return QtGui.QIcon(self._picon_path + self.index(index.row(), Column.PICON_ID).data())
        elif role == QtCore.Qt.TextAlignmentRole and column in self.CENTERED_COLUMNS:
            return QtCore.Qt.AlignCenter
        else:
            return super().data(index, role)

    @property
    def picon_path(self):
        return self._picon_path

    @picon_path.setter
    def picon_path(self, value):
        self._picon_path = value


class BouquetsModel(QtGui.QStandardItemModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dropMimeData(self, data, action, row, column, parent):
        """ Overridden to prevent child creation when dragged onto an element. """
        if row < 0:
            row = parent.row() + 1
            parent = parent.parent()

        return super().dropMimeData(data, action, row, 0, parent)


class SatelliteModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("Satellite", "Pos", "flags", "pos_value", "transponders")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS)

    def data(self, index, role):
        if role == QtCore.Qt.TextAlignmentRole and index.column() == 1:
            return QtCore.Qt.AlignCenter

        return super().data(index, role)


class SatelliteTransponderModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("Frec", "SR", "Pol", "FEC", "System", "Mod", "", "", "")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS)

    def data(self, index, role):
        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter

        return super().data(index, role)


class PiconModel(QtCore.QSortFilterProxyModel):
    HEADER_LABELS = ("Info", "", "Picon")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = QtGui.QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(self.HEADER_LABELS)
        self.setSourceModel(self.model)

    def data(self, index, role):
        if index.column() == Column.PICON_IMG and role == QtCore.Qt.DecorationRole:
            return QtGui.QIcon(self.index(index.row(), Column.PICON_PATH).data())
        return super().data(index, role)

    def appendRow(self, *__args):
        self.model.appendRow(*__args)

    def filter(self, text):
        reg = QtCore.QRegExp(text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString)
        self.setFilterRegExp(reg)
        self.setFilterKeyColumn(Column.PICON_INFO)


class EpgModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("Title", "Time", "Description", "Event")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS)


class TimerModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("Name", "Description", "Service", "Time", "Timer")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS)


class FtpModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("Name", "Size", "Date", "Attr.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS)


class FileModel(QtWidgets.QFileSystemModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.AllEntries | QtCore.QDir.NoDot)


class ServiceTypeModel(QtGui.QStandardItemModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for t in ("TV", "1"), ("TV (H264)", "22"), ("TV (HD)", "25"), ("TV (UHD)", "31"), ("Radio", "2"), ("Data", "3"):
            self.appendRow((QtGui.QStandardItem(t[0]), QtGui.QStandardItem(t[1])))
