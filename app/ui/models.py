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

__all__ = ["ServicesModel", "FavModel", "BouquetsModel", "SatellitesModel", "SatelliteUpdateModel",
           "PiconsSrcModel", "PiconsDstModel", "EpgModel", "TimerModel", "FtpModel", "FileModel"]

from PyQt5 import QtGui, QtWidgets, QtCore

from app.ui.uicommons import Column


class ServicesModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("", "", "", "Picon", "", "Name", "", "", "Package", "Type",
                     "SID", "Frec", "SR", "Pol", "FEC", "System", "Pos", "", "", "")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS)
        self._picon_path = ""

    def data(self, index, role):
        if index.column() == Column.PICON and role == QtCore.Qt.DecorationRole:
            return QtGui.QIcon(self._picon_path + self.index(index.row(), Column.PICON_ID).data())
        return super().data(index, role)

    @property
    def picon_path(self):
        return self._picon_path

    @picon_path.setter
    def picon_path(self, value):
        self._picon_path = value


class FavModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("", "", "", "Picon", "", "Name", "", "", "", "Type", "", "", "", "", "", "", "Pos", "", "", "")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS)
        self._picon_path = ""

    def dropMimeData(self, data, action, row, column, parent):
        """ Overridden to prevent data being dragged into a cell. Column -> 0. """
        return super().dropMimeData(data, action, row, 0, parent)

    def data(self, index, role):
        if index.column() == Column.PICON and role == QtCore.Qt.DecorationRole:
            return QtGui.QIcon(self._picon_path + self.index(index.row(), Column.PICON_ID).data())
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


class SatellitesModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("Satellite", "Frec", "SR", "Pol", "FEC", "System", "Mod")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS)


class SatelliteUpdateModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("Satellite", "Position", "Type")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS)


class PiconsSrcModel(QtGui.QStandardItemModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PiconsDstModel(QtGui.QStandardItemModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EpgModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("Title", "Time", "Description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS)


class TimerModel(QtGui.QStandardItemModel):
    HEADER_LABELS = ("Name", "Description", "Service", "Time")

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
