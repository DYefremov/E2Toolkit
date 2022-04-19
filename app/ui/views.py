# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2022 Dmitriy Yefremov
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

__all__ = ["ServicesView", "FavView", "BouquetsView", "SatelliteView", "TransponderView",
           "PiconView", "PiconDstView", "EpgView", "TimerView", "FtpView", "FileView", "MediaView"]

from PyQt5 import QtWidgets, QtCore, QtGui

from app.ui.models import *
from app.ui.uicommons import Column, BqGenType


class BaseTableView(QtWidgets.QTableView):
    # Main signals
    copied = QtCore.pyqtSignal(bool)
    inserted = QtCore.pyqtSignal(bool)
    removed = QtCore.pyqtSignal(dict)  # row -> id
    edited = QtCore.pyqtSignal(int)  # row index
    double_clicked = QtCore.pyqtSignal()
    # Called when the Delete key is released
    # or remove called from the context menu.
    delete_release = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(self.NoEditTriggers)
        self.setSelectionMode(self.ExtendedSelection)
        self.setSelectionBehavior(self.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)

        self.clipboard = QtWidgets.QApplication.instance().clipboard()

    def keyReleaseEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Delete and not event.isAutoRepeat():
            self.delete_release.emit()
        else:
            super().keyReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()

    def selectedIndexes(self):
        """ Overridden to get hidden column values. """
        return self.selectionModel().selectedIndexes()

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())

    def on_copy(self):
        rows = self.selectedIndexes()
        if not rows:
            return

        self.clipboard.setMimeData(self.model().mimeData(sorted(rows, reverse=True)))
        self.copied.emit(True)

    def on_paste(self):
        target = self.selectionModel().currentIndex()
        mime = self.clipboard.mimeData()
        if mime.hasFormat("application/x-qabstractitemmodeldatalist"):
            if self.model().dropMimeData(mime, QtCore.Qt.CopyAction, target.row() + 1, 0, QtCore.QModelIndex()):
                mime.clear()
                self.inserted.emit(True)

    def on_cut(self):
        self.on_copy()
        self.on_remove()

    def on_remove(self, move_cursor=False):
        model = self.model()
        selection_model = self.selectionModel()
        removed = [i.row() for i in sorted(selection_model.selectedRows(), reverse=True)]
        self.removed.emit({r: model.index(r, Column.FAV_ID).data() for r in removed})
        list(map(model.removeRow, removed))

        if move_cursor:
            i = self.moveCursor(self.MoveDown, QtCore.Qt.ControlModifier)
            selection_model.select(i, selection_model.Select | selection_model.Rows)
        else:
            self.delete_release.emit()

    def on_edit(self):
        if self.selectionModel().selectedRows():
            self.edited.emit(self.currentIndex().row())


class Searcher(QtWidgets.QWidget):
    """ Provides search possibilities. """

    def search(self, text):
        sel_model = self.selectionModel()
        sel_model.clearSelection()
        if not text:
            return

        model = self.model()
        matches = []
        for c in self.search_columns():
            start = model.index(0, c)
            matches.extend(model.match(start, QtCore.Qt.DisplayRole, text, -1, QtCore.Qt.MatchContains))
        if matches:
            mode = sel_model.Select | sel_model.Rows
            for m in matches:
                sel_model.select(m, mode)
            # Scrolling to first founded index.
            self.scrollTo(matches[0])

    def search_columns(self):
        return [Column.NAME]


class PiconAssignment(QtWidgets.QWidget):
    """ Additional class [mixin] for assigning picons. """

    def assign_picon(self):
        rows = self.selectionModel().selectedRows(Column.PICON_ID)
        if not rows:
            return

        resp = QtWidgets.QFileDialog.getOpenFileName(self, self.tr("Select *.png file"), "", "PNG files (*.png)")
        if all(resp):
            self.picon_assigned.emit((resp[0], [r.data() for r in rows]))

    def copy_reference(self):
        cur_index = self.selectionModel().currentIndex()
        if not cur_index.isValid():
            return

        p_id = self.model().index(cur_index.row(), Column.PICON_ID).data()
        if p_id:
            self.clipboard.setText(p_id.rstrip(".png"))


class BaseTreeView(QtWidgets.QTreeView):
    copied = QtCore.pyqtSignal(bool)
    inserted = QtCore.pyqtSignal(bool)
    removed = QtCore.pyqtSignal(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(self.NoEditTriggers)
        self.setSelectionMode(self.ExtendedSelection)
        self.setSelectionBehavior(self.SelectRows)
        # We will use it as a local clipboard.
        self.clipboard = []
        # Drag and Drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(self.InternalMove)

    def selectedIndexes(self):
        """ Overridden to get hidden column values. """
        return self.selectionModel().selectedIndexes()

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())

    def on_copy(self):
        indexes = self.selectedIndexes()
        if not indexes:
            return

        indexes = sorted(filter(lambda i: i.parent() and i.parent().row() >= 0, indexes), reverse=True)
        mime = self.model().mimeData(indexes)
        if mime:
            self.clipboard.append(mime)
            self.copied.emit(True)

    def on_paste(self):
        if not self.clipboard:
            return

        target = self.selectionModel().currentIndex()
        target_row = target.row() + 1
        target_index = target.parent()
        # Root element.
        if target.parent().row() == -1:
            target_index = target
            target_row = 0

        mime = self.clipboard.pop()
        if mime and mime.hasFormat("application/x-qabstractitemmodeldatalist"):
            if self.model().dropMimeData(mime, QtCore.Qt.CopyAction, target_row, 0, target_index):
                self.inserted.emit(True)

    def on_cut(self):
        self.on_copy()
        self.on_remove()

    def on_remove(self, move_cursor=False, root=False):
        """ Removes elements from tree.

            When root=True -> allowed to delete root elements.
        """
        model = self.model()
        selection_model = self.selectionModel()
        removed = [(i.row(), i.parent()) for i in sorted(selection_model.selectedRows(), reverse=True) if
                   (i.parent() and i.parent().row() >= 0) or root]
        self.removed.emit([[model.index(r[0], c, r[1]) for c in range(model.columnCount(r[1]))] for r in removed])
        list(map(lambda r: model.removeRow(*r), removed))

        if move_cursor:
            i = self.moveCursor(self.MoveDown, QtCore.Qt.ControlModifier)
            selection_model.select(i, selection_model.Select | selection_model.Rows)


class ServicesView(BaseTableView, PiconAssignment, Searcher):
    """ Main class for services list. """
    picon_assigned = QtCore.pyqtSignal(tuple)  # tuple -> src, picon ids
    gen_bouquets = QtCore.pyqtSignal(BqGenType)

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
        self.setSortingEnabled(True)
        self.setObjectName("services_view")
        # Model
        self.setModel(ServicesModel(self))
        # Picons size.
        self.setIconSize(QtCore.QSize(32, 32))
        # Setting visible columns.
        for c in (Column.CAS_FLAGS, Column.STANDARD, Column.CODED, Column.LOCKED, Column.HIDE, Column.PICON_ID,
                  Column.DATA_ID, Column.FAV_ID, Column.DATA_ID, Column.TRANSPONDER):
            self.setColumnHidden(c, True)

        self.setColumnWidth(Column.PICON, 50)
        self.setColumnWidth(Column.NAME, 150)
        self.setColumnWidth(Column.TYPE, 75)
        self.setColumnWidth(Column.SSID, 50)
        self.setColumnWidth(Column.FREQ, 75)
        self.setColumnWidth(Column.RATE, 75)
        self.setColumnWidth(Column.POL, 50)
        self.setColumnWidth(Column.FEC, 50)
        self.setColumnWidth(Column.SYSTEM, 75)
        self.setColumnWidth(Column.POS, 50)
        # Drag and Drop
        self.setDragEnabled(True)
        # Context [popup] menu.
        self.context_menu = self.ContextMenu(self)
        self.init_actions()

    def init_actions(self):
        self.context_menu.remove_action.triggered.connect(self.on_remove)
        self.context_menu.copy_action.triggered.connect(self.on_copy)
        self.context_menu.edit_action.triggered.connect(self.on_edit)
        self.context_menu.copy_ref_action.triggered.connect(self.copy_reference)
        self.context_menu.assign_action.triggered.connect(self.assign_picon)
        self.context_menu.create_bq_for_current_sat_action.triggered.connect(
            lambda b: self.gen_bouquets.emit(BqGenType.SAT))
        self.context_menu.create_bq_for_current_package_action.triggered.connect(
            lambda b: self.gen_bouquets.emit(BqGenType.PACKAGE))
        self.context_menu.create_bq_for_current_type_action.triggered.connect(
            lambda b: self.gen_bouquets.emit(BqGenType.TYPE))
        self.context_menu.create_bq_for_each_sat_action.triggered.connect(
            lambda b: self.gen_bouquets.emit(BqGenType.EACH_SAT))
        self.context_menu.create_bq_for_each_package_action.triggered.connect(
            lambda b: self.gen_bouquets.emit(BqGenType.EACH_PACKAGE))
        self.context_menu.create_bq_for_each_type_action.triggered.connect(
            lambda b: self.gen_bouquets.emit(BqGenType.EACH_TYPE))

    def contextMenuEvent(self, event):
        self.context_menu.popup(QtGui.QCursor.pos())

    def keyPressEvent(self, event):
        key = event.key()
        ctrl = event.modifiers() == QtCore.Qt.ControlModifier

        if ctrl and key == QtCore.Qt.Key_C:
            self.on_copy()
        elif key == QtCore.Qt.Key_Delete:
            self.on_remove(True)
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            self.edited.emit(index.row())

    def search_columns(self):
        return Column.NAME, Column.PACKAGE


class FavView(BaseTableView, PiconAssignment, Searcher):
    """ Main class for favorites list. """
    picon_assigned = QtCore.pyqtSignal(tuple)
    locate_service = QtCore.pyqtSignal(str)
    insert_marker = QtCore.pyqtSignal()
    insert_space = QtCore.pyqtSignal()

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
            self.paste_action.setEnabled(False)
            self.addAction(self.paste_action)
            self.addSeparator()
            icon = QtGui.QIcon.fromTheme("document-edit")
            self.edit_action = QtWidgets.QAction(icon, self.tr("Edit"), self)
            self.addAction(self.edit_action)
            icon = QtGui.QIcon.fromTheme("document-edit")
            self.set_extra_name_action = QtWidgets.QAction(icon, self.tr("Rename for this bouquet"), self)
            self.addAction(self.set_extra_name_action)
            icon = QtGui.QIcon.fromTheme("document-revert")
            self.set_default_name_action = QtWidgets.QAction(icon, self.tr("Set default name"), self)
            self.addAction(self.set_default_name_action)
            icon = QtGui.QIcon.fromTheme("edit-find")
            self.locate_action = QtWidgets.QAction(icon, self.tr("Locate in services"), self)
            self.addAction(self.locate_action)
            icon = QtGui.QIcon.fromTheme("format-text-bold")
            self.mark_duplicates_action = QtWidgets.QAction(icon, self.tr("Mark duplicates"), self)
            self.addAction(self.mark_duplicates_action)
            self.addSeparator()
            icon = QtGui.QIcon.fromTheme("insert-text")
            self.insert_marker_action = QtWidgets.QAction(icon, self.tr("Insert marker"), self)
            self.addAction(self.insert_marker_action)
            icon = QtGui.QIcon.fromTheme("format-text-underline")
            self.insert_space_action = QtWidgets.QAction(icon, self.tr("Insert space"), self)
            self.addAction(self.insert_space_action)
            self.addSeparator()
            icon = QtGui.QIcon.fromTheme("edit-copy")
            self.copy_ref_action = QtWidgets.QAction(icon, self.tr("Copy reference"), self)
            self.addAction(self.copy_ref_action)
            self.assign_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("insert-image"), self.tr("Assign picon"), self)
            self.addAction(self.assign_action)
            self.addSeparator()
            self.remove_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("list-remove"), self.tr("Remove"), self)
            self.remove_action.setShortcut("Del")
            self.addAction(self.remove_action)
            # Disabled [hidden] actions.
            self.set_extra_name_action.setVisible(False)
            self.set_default_name_action.setVisible(False)
            self.mark_duplicates_action.setVisible(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("fav_view")
        self.setModel(FavModel(self))
        # Setting visible columns.
        for c in (Column.CAS_FLAGS, Column.STANDARD, Column.CODED, Column.LOCKED, Column.HIDE, Column.PACKAGE,
                  Column.PICON_ID, Column.SSID, Column.FREQ, Column.RATE, Column.POL, Column.FEC, Column.SYSTEM,
                  Column.DATA_ID, Column.FAV_ID, Column.TRANSPONDER):
            self.setColumnHidden(c, True)

        self.setIconSize(QtCore.QSize(32, 32))
        self.setColumnWidth(Column.PICON, 50)
        self.setColumnWidth(Column.NAME, 150)
        self.setColumnWidth(Column.TYPE, 75)
        self.setColumnWidth(Column.POS, 50)
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
        self.context_menu.copy_action.triggered.connect(self.on_copy)
        self.context_menu.paste_action.triggered.connect(self.on_paste)
        self.context_menu.cut_action.triggered.connect(self.on_cut)
        self.context_menu.edit_action.triggered.connect(self.on_edit)
        self.context_menu.locate_action.triggered.connect(self.on_locate_service)
        self.context_menu.copy_ref_action.triggered.connect(self.copy_reference)
        self.context_menu.assign_action.triggered.connect(self.assign_picon)
        # Copy - Paste items.
        self.copied.connect(self.context_menu.paste_action.setEnabled)
        self.inserted.connect(self.context_menu.paste_action.setDisabled)
        self.copied.connect(self.context_menu.copy_action.setDisabled)
        self.inserted.connect(self.context_menu.copy_action.setEnabled)
        # Marker\Space.
        self.context_menu.insert_marker_action.triggered.connect(self.insert_marker.emit)
        self.context_menu.insert_space_action.triggered.connect(self.insert_space.emit)

    def contextMenuEvent(self, event):
        self.context_menu.popup(QtGui.QCursor.pos())

    def on_locate_service(self):
        fav_id = self.model().index(self.selectionModel().currentIndex().row(), Column.FAV_ID).data()
        if fav_id:
            self.locate_service.emit(fav_id)

    def dropEvent(self, event):
        super().dropEvent(event)
        self.inserted.emit(True)

    def keyPressEvent(self, event):
        key = event.key()
        ctrl = event.modifiers() == QtCore.Qt.ControlModifier

        if ctrl and key == QtCore.Qt.Key_X:
            self.on_cut()
        elif ctrl and key == QtCore.Qt.Key_C:
            self.on_copy()
        elif ctrl and key == QtCore.Qt.Key_V:
            self.on_paste()
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


class BouquetsView(BaseTreeView):
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
            # Disabled [hidden] actions.
            self.import_action.setVisible(False)
            self.export_action.setVisible(False)

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
        self.context_menu.copy_action.triggered.connect(self.on_copy)
        self.context_menu.paste_action.triggered.connect(self.on_paste)
        self.context_menu.cut_action.triggered.connect(self.on_cut)
        self.context_menu.remove_action.triggered.connect(self.on_remove)

    def contextMenuEvent(self, event):
        self.context_menu.popup(QtGui.QCursor.pos())

    def keyPressEvent(self, event):
        key = event.key()
        ctrl = event.modifiers() == QtCore.Qt.ControlModifier

        if ctrl and key == QtCore.Qt.Key_X:
            self.on_cut()
        elif ctrl and key == QtCore.Qt.Key_C:
            self.on_copy()
        elif ctrl and key == QtCore.Qt.Key_V:
            self.on_paste()
        elif key == QtCore.Qt.Key_Delete:
            self.on_remove(True)
        else:
            super().keyPressEvent(event)


class BaseSatelliteView(BaseTableView):
    add = QtCore.pyqtSignal()

    class ContextMenu(QtWidgets.QMenu):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.new_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("list-add"), self.tr("Add"), self)
            self.addAction(self.new_action)
            self.edit_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-edit"), self.tr("Edit"), self)
            self.addAction(self.edit_action)
            self.addSeparator()
            self.remove_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("list-remove"), self.tr("Remove"), self)
            self.remove_action.setShortcut("Del")
            self.addAction(self.remove_action)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("base_satellite_view")

        self.context_menu = self.ContextMenu(self)
        self.init_actions()

    def init_actions(self):
        self.context_menu.new_action.triggered.connect(self.add.emit)
        self.context_menu.edit_action.triggered.connect(self.on_edit)
        self.context_menu.remove_action.triggered.connect(self.on_remove)

    def contextMenuEvent(self, event):
        if self.model().rowCount():
            self.context_menu.popup(QtGui.QCursor.pos())

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Delete:
            self.remove()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            self.edited.emit(index.row())

    def remove(self):
        self.on_remove(True)


class SatelliteView(BaseSatelliteView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("satellite_view")

        self.setModel(SatelliteModel(self))
        header = self.horizontalHeader()
        header.setSectionHidden(Column.SAT_DATA, True)
        header.setSectionResizeMode(0, header.Stretch)
        header.setMinimumSectionSize(128)
        header.setStretchLastSection(False)


class TransponderView(BaseSatelliteView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(self.MultiSelection)
        self.setObjectName("transponder_view")

        self.setModel(SatelliteTransponderModel(self))
        header = self.horizontalHeader()
        header.setSectionHidden(6, True)
        header.setSectionHidden(7, True)
        header.setSectionHidden(8, True)


class PiconView(BaseTableView):
    replaced = QtCore.pyqtSignal(tuple)  # tuple -> self, paths
    id_received = QtCore.pyqtSignal(tuple)  # tuple -> self, picon ids
    urls_received = QtCore.pyqtSignal(tuple)  # tuple -> self, urls
    remove_from_receiver = QtCore.pyqtSignal(list)  # -> row nums

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("picon_view")

        self.setModel(PiconModel())
        self.setIconSize(QtCore.QSize(96, 96))
        v_header = self.verticalHeader()
        v_header.setMinimumSectionSize(96)
        v_header.setSectionResizeMode(v_header.Stretch)

        header = self.horizontalHeader()
        header.setSectionHidden(Column.PICON_PATH, True)
        header.setSectionResizeMode(0, header.Stretch)
        header.setMinimumSectionSize(128)
        header.setStretchLastSection(False)

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropOverwriteMode(False)
        self.setDefaultDropAction(QtCore.Qt.CopyAction)

    def dragEnterEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls() or mime_data.hasFormat("application/x-qabstractitemmodeldatalist"):
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls() or mime_data.hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            self.urls_received.emit((self, mime_data.urls()))
        elif mime_data.hasFormat("application/x-qabstractitemmodeldatalist"):
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            src_model = QtGui.QStandardItemModel()
            src_model.dropMimeData(event.mimeData(), QtCore.Qt.CopyAction, 0, 0, QtCore.QModelIndex())
            row_count = src_model.rowCount()

            source = type(event.source())
            if source is FavView:
                self.id_received.emit((self, [src_model.item(r, Column.PICON_ID).text() for r in range(row_count)]))
            elif source is PiconView:
                self.replaced.emit((self, [src_model.item(r, Column.PICON_PATH).text() for r in range(row_count)]))
        else:
            event.ignore()


class PiconDstView(PiconView):
    class ContextMenu(QtWidgets.QMenu):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.remove_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("list-remove"), self.tr("Remove files"), self)
            self.remove_action.setShortcut("Del")
            self.addAction(self.remove_action)
            self.addSeparator()
            self.remove_from_receiver_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("user-trash"),
                                                                 self.tr("Remove from the receiver"), self)
            self.addAction(self.remove_from_receiver_action)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("picon_dst_view")

        self.context_menu = self.ContextMenu(self)
        self.init_actions()

    def init_actions(self):
        self.context_menu.remove_action.triggered.connect(self.on_remove_files)
        self.context_menu.remove_from_receiver_action.triggered.connect(self.on_remove_from_receiver)

    def contextMenuEvent(self, event):
        if self.model().rowCount():
            self.context_menu.popup(QtGui.QCursor.pos())

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Delete:
            self.on_remove_files()
        else:
            super().keyPressEvent(event)

    def on_remove_files(self):
        if QtWidgets.QMessageBox.question(self, "", self.tr("Are you sure?")) != QtWidgets.QMessageBox.Yes:
            return

        self.on_remove()

    def on_remove_from_receiver(self):
        if QtWidgets.QMessageBox.question(self, "", self.tr("Are you sure?")) != QtWidgets.QMessageBox.Yes:
            return

        self.remove_from_receiver.emit([r.row() for r in self.selectionModel().selectedRows()])


class EpgView(BaseTableView, Searcher):
    timer_add = QtCore.pyqtSignal(int)

    class ContextMenu(QtWidgets.QMenu):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.add_timer_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("list-add"), self.tr("Add timer"), self)
            self.addAction(self.add_timer_action)

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
        self.setColumnHidden(Column.EPG_EVENT, True)
        self.context_menu = self.ContextMenu(self)
        self.init_actions()

    def init_actions(self):
        self.context_menu.add_timer_action.triggered.connect(lambda b: self.on_add_timer())

    def mouseDoubleClickEvent(self, event):
        self.on_add_timer(self.indexAt(event.pos()))

    def contextMenuEvent(self, event):
        if self.model().rowCount():
            self.context_menu.popup(QtGui.QCursor.pos())

    def on_add_timer(self, index=None):
        if not index:
            index = self.selectionModel().currentIndex()

        if not index.isValid():
            return

        self.timer_add.emit(index.row())

    def search_columns(self):
        return Column.EPG_TITLE, Column.EPG_DESC, Column.EPG_TIME


class TimerView(BaseTableView, Searcher):
    class ContextMenu(QtWidgets.QMenu):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.edit_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-edit"), self.tr("Edit"), self)
            self.addAction(self.edit_action)
            self.addSeparator()
            self.remove_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("list-remove"), self.tr("Remove"), self)
            self.remove_action.setShortcut("Del")
            self.addAction(self.remove_action)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(self.ContiguousSelection)
        self.setSortingEnabled(True)
        self.horizontalHeader().setMinimumSectionSize(200)
        self.horizontalHeader().setStretchLastSection(True)
        self.setObjectName("timer_view")

        self.setModel(TimerModel(self))
        self.setColumnHidden(Column.TIMER_DATA, True)
        self.context_menu = self.ContextMenu(self)
        self.init_actions()

    def init_actions(self):
        self.context_menu.edit_action.triggered.connect(self.on_edit)
        self.context_menu.remove_action.triggered.connect(self.on_remove)

    def contextMenuEvent(self, event):
        if self.model().rowCount():
            self.context_menu.popup(QtGui.QCursor.pos())

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            self.edited.emit(index.row())

    def search_columns(self):
        return Column.TIMER_NAME, Column.TIMER_DESC, Column.TIMER_SRV, Column.TIMER_TIME


class FtpView(QtWidgets.QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(self.NoEditTriggers)
        self.setObjectName("ftp_view")
        self.setShowGrid(False)
        self.setSelectionBehavior(self.SelectRows)
        self.verticalHeader().setVisible(False)

        self.setModel(FtpModel(self))

    def clear_data(self):
        model = self.model()
        model.removeRows(0, model.rowCount())


class FileView(QtWidgets.QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("file_view")
        self.setShowGrid(False)
        self.setSelectionBehavior(self.SelectRows)
        self.verticalHeader().setVisible(False)
        # Init root path
        root_path = QtCore.QDir.rootPath()
        model = FileModel(self)
        model.setRootPath(root_path)
        self.setModel(model)
        self.setRootIndex(model.index(root_path))

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Return:
            self.change_path(self.currentIndex())
        elif key == QtCore.Qt.Key_Delete:
            self.on_remove(True)
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            self.change_path(index)

    def change_path(self, index):
        model = self.model()
        if model.isDir(index):
            path = self.model().data(index)
            if path == "..":
                self.setRootIndex(self.rootIndex().parent())
            else:
                if self.model().hasChildren(index):
                    self.setRootIndex(index)


class MediaView(QtWidgets.QGraphicsView):
    """ Media playback view. """
    double_clicked = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAutoFillBackground(True)
        self.setInteractive(True)
        self.setAlignment(QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.setCacheMode(QtWidgets.QGraphicsView.CacheNone)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: black; border: 2px solid black")
        self.setObjectName("media_view")
        # Mouse cursor hide timer.
        self.cursor_hide_timer = QtCore.QTimer(self)
        self.cursor_hide_timer.setSingleShot(True)
        self.cursor_hide_timer.timeout.connect(lambda: self.setCursor(QtCore.Qt.BlankCursor))

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()

    def mouseMoveEvent(self, event):
        self.setCursor(QtCore.Qt.ArrowCursor)
        self.cursor_hide_timer.start(3000)


class BackupFileView(QtWidgets.QTableView):
    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("backup_view")
        self.setEditTriggers(self.NoEditTriggers)
        self.setSelectionBehavior(self.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)

        model = QtWidgets.QFileSystemModel(self)
        model.setReadOnly(True)
        model.setRootPath(path)
        self.setModel(model)
        self.setRootIndex(model.index(model.rootPath()))

        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 100)
        self.setColumnHidden(2, True)
