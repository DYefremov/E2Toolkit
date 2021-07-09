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

from PyQt5 import QtWidgets, QtCore, QtGui

from app.ui.models import *
from app.ui.uicommons import Column


class BaseTableView(QtWidgets.QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(self.NoEditTriggers)
        self.setSelectionBehavior(self.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())

    def on_remove(self, move_cursor=False):
        model = self.model()
        selection_model = self.selectionModel()
        for i in sorted(selection_model.selectedRows(), reverse=True):
            model.removeRow(i.row())

        if move_cursor:
            i = self.moveCursor(self.MoveDown, QtCore.Qt.ControlModifier)
            selection_model.select(i, selection_model.Select | selection_model.Rows)


class ServicesView(BaseTableView):
    class ContextMenu(QtWidgets.QMenu):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.copy_to_top_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("go-top"), self.tr("To the top"), self)
            self.addAction(self.copy_to_top_action)
            self.copy_to_end_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("go-bottom"), self.tr("To the end"), self)
            self.addAction(self.copy_to_end_action)

            # Create bouquet submenu.
            self.create_bouquet_menu = QtWidgets.QMenu("Create bouquet", self)
            self.addMenu(self.create_bouquet_menu)
            self.create_bq_for_current_sat_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-new"),
                                                                      self.tr("For current satellite"),
                                                                      self.create_bouquet_menu)
            self.create_bouquet_menu.addAction(self.create_bq_for_current_sat_action)
            self.create_bq_for_current_package_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-new"),
                                                                          self.tr("For current package"),
                                                                          self.create_bouquet_menu)
            self.create_bouquet_menu.addAction(self.create_bq_for_current_package_action)
            self.create_bq_for_current_type_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-new"),
                                                                       self.tr("For current type"),
                                                                       self.create_bouquet_menu)
            self.create_bouquet_menu.addAction(self.create_bq_for_current_type_action)
            self.create_bouquet_menu.addSeparator()
            self.create_bq_for_each_sat_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-select-all"),
                                                                   self.tr("For each satellite"),
                                                                   self.create_bouquet_menu)
            self.create_bouquet_menu.addAction(self.create_bq_for_each_sat_action)
            self.create_bq_for_each_package_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-select-all"),
                                                                       self.tr("For each package"),
                                                                       self.create_bouquet_menu)
            self.create_bouquet_menu.addAction(self.create_bq_for_each_package_action)
            self.create_bq_for_each_type_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-select-all"),
                                                                    self.tr("For each type"),
                                                                    self.create_bouquet_menu)
            self.create_bouquet_menu.addAction(self.create_bq_for_each_type_action)

            self.copy_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-copy"), self.tr("Copy"), self)
            self.copy_action.setShortcut("Ctrl+C")
            self.addAction(self.copy_action)
            self.edit_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-edit"), self.tr("Edit"), self)
            self.addAction(self.edit_action)
            self.addSeparator()
            self.copy_ref_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-copy"),
                                                     self.tr("Copy reference"), self)
            self.addAction(self.copy_ref_action)
            self.assign_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("insert-image"), self.tr("Assign picon"), self)
            self.addAction(self.assign_action)
            self.addSeparator()
            self.remove_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("list-remove"), self.tr("Remove"), self)
            self.remove_action.setShortcut("Del")
            self.addAction(self.remove_action)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(self.ExtendedSelection)
        self.setSortingEnabled(True)
        self.setObjectName("services_view")
        # Model
        self.setModel(ServicesModel(self))
        # Setting visible columns.
        for c in (Column.CAS_FLAGS, Column.STANDARD, Column.CODED, Column.LOCKED, Column.HIDE, Column.PICON_ID,
                  Column.DATA_ID, Column.FAV_ID, Column.DATA_ID, Column.TRANSPONDER):
            self.setColumnHidden(c, True)

        # Drag and Drop
        self.setDragEnabled(True)
        # Context [popup] menu.
        self.context_menu = self.ContextMenu(self)
        self.init_actions()

    def init_actions(self):
        self.context_menu.remove_action.triggered.connect(self.on_remove)

    def contextMenuEvent(self, event):
        self.context_menu.popup(QtGui.QCursor.pos())

    def selectedIndexes(self):
        """ Overridden to get hidden column values. """
        return self.selectionModel().selectedIndexes()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        if key == QtCore.Qt.Key_Delete:
            self.on_remove(True)
        else:
            super().keyPressEvent(event)


class FavView(BaseTableView):
    class ContextMenu(QtWidgets.QMenu):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.cut_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-cut"), self.tr("Cut"), self)
            self.cut_action.setShortcut("Ctrl+X")
            self.addAction(self.cut_action)
            self.copy_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-copy"), self.tr("Copy"), self)
            self.copy_action.setShortcut("Ctrl+C")
            self.addAction(self.copy_action)
            self.paste_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-paste"), self.tr("Paste"), self)
            self.paste_action.setShortcut("Ctrl+V")
            self.addAction(self.paste_action)
            self.addSeparator()
            self.edit_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-edit"), self.tr("Edit"), self)
            self.addAction(self.edit_action)
            self.set_extra_name_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-edit"),
                                                           self.tr("Rename for this bouquet"), self)
            self.addAction(self.set_extra_name_action)
            self.set_default_name_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-revert"),
                                                             self.tr("Set default name"), self)
            self.addAction(self.set_default_name_action)
            self.addSeparator()
            self.locate_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-find"), self.tr("Locate in services"),
                                                   self)
            self.addAction(self.locate_action)
            self.mark_duplicates_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("format-text-bold"),
                                                            self.tr("Mark duplicates"), self)
            self.addAction(self.mark_duplicates_action)
            self.insert_marker_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("insert-text"),
                                                          self.tr("Insert marker"), self)
            self.addAction(self.insert_marker_action)
            self.insert_space_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("format-text-underline"),
                                                         self.tr("Insert space"), self)
            self.addAction(self.insert_space_action)
            self.addSeparator()
            self.copy_ref_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-copy"), self.tr("Copy reference"),
                                                     self)
            self.addAction(self.copy_ref_action)
            self.assign_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("insert-image"), self.tr("Assign picon"), self)
            self.addAction(self.assign_action)
            self.addSeparator()
            self.remove_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("list-remove"), self.tr("Remove"), self)
            self.remove_action.setShortcut("Del")
            self.addAction(self.remove_action)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(self.ExtendedSelection)
        self.setObjectName("fav_view")

        self.setModel(FavModel(self))
        # Setting visible columns.
        for c in (Column.CAS_FLAGS, Column.STANDARD, Column.CODED, Column.LOCKED, Column.HIDE, Column.PACKAGE,
                  Column.PICON_ID, Column.SSID, Column.FREQ, Column.RATE, Column.POL, Column.FEC, Column.SYSTEM,
                  Column.DATA_ID, Column.FAV_ID, Column.TRANSPONDER):
            self.setColumnHidden(c, True)

        # Drag and Drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.verticalHeader().setSectionsMovable(True)
        # Context menu.
        self.context_menu = self.ContextMenu(self)
        self.init_actions()

    def init_actions(self):
        self.context_menu.remove_action.triggered.connect(self.on_remove)

    def contextMenuEvent(self, event):
        self.context_menu.popup(QtGui.QCursor.pos())

    def selectedIndexes(self):
        """ Overridden to get hidden column values. """
        return self.selectionModel().selectedIndexes()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        ctrl = event.modifiers() == QtCore.Qt.ControlModifier

        if ctrl and key == QtCore.Qt.Key_Up:
            self.move_up()
        elif ctrl and key == QtCore.Qt.Key_Down:
            self.move_down()
        elif key == QtCore.Qt.Key_Delete:
            self.on_remove(True)
        else:
            super().keyPressEvent(event)

    def move_up(self):
        pass

    def move_down(self):
        pass


class BouquetsView(QtWidgets.QTreeView):
    class ContextMenu(QtWidgets.QMenu):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.new_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-new"), self.tr("New"), self)
            self.addAction(self.new_action)
            self.import_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-open"), self.tr("Import"), self)
            self.addAction(self.import_action)
            self.export_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-save-as"), self.tr("Save as..."),
                                                   self)
            self.addAction(self.export_action)
            self.addSeparator()
            self.cut_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-cut"), self.tr("Cut"), self)
            self.cut_action.setShortcut("Ctrl+X")
            self.addAction(self.cut_action)
            self.copy_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-copy"), self.tr("Copy"), self)
            self.copy_action.setShortcut("Ctrl+C")
            self.addAction(self.copy_action)
            self.paste_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-paste"), self.tr("Paste"), self)
            self.paste_action.setShortcut("Ctrl+V")
            self.addAction(self.paste_action)
            self.addSeparator()
            self.edit_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-edit"), self.tr("Edit"), self)
            self.addAction(self.edit_action)
            self.addSeparator()
            self.remove_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("list-remove"), self.tr("Remove"), self)
            self.remove_action.setShortcut("Del")
            self.addAction(self.remove_action)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(self.NoEditTriggers)
        self.setHeaderHidden(True)
        self.setObjectName("bouquets_view")

        self.setModel(BouquetsModel(self))
        # Context menu.
        self.context_menu = self.ContextMenu(self)
        self.init_actions()

    def init_actions(self):
        self.context_menu.remove_action.triggered.connect(self.on_remove)

    def contextMenuEvent(self, event):
        self.context_menu.popup(QtGui.QCursor.pos())

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())

    def on_remove(self):
        pass


class SatellitesView(QtWidgets.QTreeView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(self.NoEditTriggers)
        self.setSelectionMode(self.ContiguousSelection)
        self.setHorizontalScrollMode(self.ScrollPerItem)
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
        self.setEditTriggers(self.NoEditTriggers)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)
        self.setResizeMode(self.Fixed)
        self.setObjectName("satellite_update_view")

        self.setModel(SatelliteUpdateModel(self))

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())


class PiconSrcView(BaseTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(self.ExtendedSelection)
        self.setObjectName("picon_src_view")


class PiconDstView(BaseTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(self.ExtendedSelection)
        self.setObjectName("picon_dst_view")


class EpgView(BaseTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(self.SingleSelection)
        self.setAlternatingRowColors(True)
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(200)
        header.setDefaultAlignment(QtCore.Qt.AlignCenter)
        self.setObjectName("epg_view")

        self.setModel(EpgModel(self))


class TimerView(BaseTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(self.ContiguousSelection)
        self.setSortingEnabled(True)
        self.horizontalHeader().setMinimumSectionSize(200)
        self.horizontalHeader().setStretchLastSection(True)
        self.setObjectName("timer_view")

        self.setModel(TimerModel(self))


class FtpView(QtWidgets.QListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(self.NoEditTriggers)
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
