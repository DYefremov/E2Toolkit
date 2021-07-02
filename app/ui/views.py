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

__all__ = ["ServicesView", "FavView", "BouquetsView", "SatellitesView", "SatelliteUpdateView",
           "PiconSrcView", "PiconDstView", "EpgView", "TimerView", "FtpView", "FileView"]

from PyQt5 import QtWidgets, QtCore

from app.ui.models import *
from app.ui.uicommons import Column


class ServicesView(QtWidgets.QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)
        self.setObjectName("services_view")
        # Model
        self.setModel(ServicesModel(self))
        # Setting visible columns.
        for c in (Column.SRV_CAS_FLAGS, Column.SRV_STANDARD, Column.SRV_CODED, Column.SRV_LOCKED, Column.SRV_HIDE,
                  Column.SRV_PICON_ID, Column.SRV_DATA_ID, Column.SRV_FAV_ID, Column.SRV_DATA_ID,
                  Column.SRV_TRANSPONDER):
            self.setColumnHidden(c, True)

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())


class FavView(QtWidgets.QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setObjectName("fav_view")

        self.setModel(FavModel(self))
        # Setting visible columns.
        for c in (Column.FAV_CODED, Column.FAV_LOCKED, Column.FAV_HIDE, Column.FAV_ID):
            self.setColumnHidden(c, True)

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())


class BouquetsView(QtWidgets.QTreeView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setHeaderHidden(True)
        self.setObjectName("bouquets_view")

        self.setModel(BouquetsModel(self))

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())


class SatellitesView(QtWidgets.QTreeView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerItem)
        self.setObjectName("satellite_view")

        header = self.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setCascadingSectionResizes(False)
        header.setMinimumSectionSize(100)
        header.setStretchLastSection(True)

        self.setModel(SatellitesModel(self))

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())


class SatelliteUpdateView(QtWidgets.QListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setResizeMode(QtWidgets.QListView.Fixed)
        self.setObjectName("satellite_update_view")

        self.setModel(SatelliteUpdateModel(self))

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())


class PiconSrcView(QtWidgets.QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setObjectName("picon_src_view")


class PiconDstView(QtWidgets.QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setObjectName("picon_dst_view")


class EpgView(QtWidgets.QListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setObjectName("epg_view")

        self.setModel(EpgModel(self))

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())


class TimerView(QtWidgets.QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)
        self.horizontalHeader().setMinimumSectionSize(200)
        self.horizontalHeader().setStretchLastSection(True)
        self.setObjectName("timer_view")

        self.setModel(TimerModel(self))

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())


class FtpView(QtWidgets.QListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setObjectName("ftp_view")

        self.setModel(FtpModel(self))

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())


class FileView(QtWidgets.QListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("file_view")
        # Init root path
        root_path = QtCore.QDir.rootPath()
        model = FileModel(self)
        model.setRootPath(root_path)
        self.setModel(model)
        self.setRootIndex(model.index(root_path))
