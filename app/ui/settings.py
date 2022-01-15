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


""" Main settings module. """
import os
import sys
from collections import OrderedDict
from copy import deepcopy
from enum import Enum
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QSettings, QSize, QStringListModel, QCoreApplication, pyqtSignal
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QDialog, QMessageBox, QDialogButtonBox, QFileDialog

from app.commons import APP_NAME
from app.ui.dialogs import InputDialog
from app.ui.uicommons import UI_PATH

IS_DARWIN = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"
IS_LINUX = sys.platform == "linux"


class Settings(QSettings):
    """ Base settings class. """

    class Default(Enum):
        """ Default settings """
        HOME_PATH = str(Path.home())
        DATA_PATH = f"{HOME_PATH}/{APP_NAME}/data/"
        BACKUP_PATH = f"{DATA_PATH}backup/"
        PICON_PATH = f"{DATA_PATH}picons/"
        BOX_PICON_PATH = "/usr/share/enigma2/picon/"
        BOX_SERVICES_PATH = "/etc/enigma2/"
        BOX_SATELLITE_PATH = "/etc/tuxbox/"

        USER = "root"
        PASSWORD = ""
        HOST = "127.0.0.1"
        FTP_PORT = "21"
        HTTP_PORT = "80"
        TELNET_PORT = "23"
        HTTP_USE_SSL = False

        APP_WINDOW_SIZE = QSize(850, 560)
        APP_LOCALE = "en"
        STREAM_LIB = "VLC"

        PROFILE_NAME = "Default"
        PROFILE = {"name": PROFILE_NAME,
                   "user": USER,
                   "password": PASSWORD,
                   "host": HOST,
                   "ftp_port": FTP_PORT,
                   "http_port": HTTP_PORT,
                   "telnet_port": TELNET_PORT,
                   "http_use_ssl": HTTP_USE_SSL,
                   "box_picon_path": BOX_PICON_PATH}

        PICON_PATHS = ("/usr/share/enigma2/picon/",
                       "/media/hdd/picon/",
                       "/media/usb/picon/",
                       "/media/mmc/picon/",
                       "/media/cf/picon/")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_profile = self.Default.PROFILE.value

    # ******************** Application ******************** #

    @property
    def app_window_size(self):
        return self.value("app_window_size", self.Default.APP_WINDOW_SIZE.value)

    @app_window_size.setter
    def app_window_size(self, value):
        self.setValue("app_window_size", value)

    @property
    def app_locale(self):
        return self.value("app_locale", self.Default.APP_LOCALE.value)

    @app_locale.setter
    def app_locale(self, value):
        self.setValue("app_locale", value)

    @property
    def load_last_config(self):
        return self.value("load_last_config", False, bool)

    @load_last_config.setter
    def load_last_config(self, value):
        self.setValue("load_last_config", value)

    @property
    def last_config(self):
        return self.value("last_config", {}, dict)

    @last_config.setter
    def last_config(self, value):
        self.setValue("last_config", value)

    @property
    def show_srv_hints(self):
        return self.value("show_srv_hints", True, bool)

    @show_srv_hints.setter
    def show_srv_hints(self, value):
        self.setValue("show_srv_hints", value)

    @property
    def show_fav_hints(self):
        return self.value("show_fav_hints", True, bool)

    @show_fav_hints.setter
    def show_fav_hints(self, value):
        self.setValue("show_fav_hints", value)

    @property
    def backup_before_save(self):
        return self.value("backup_before_save", True, bool)

    @backup_before_save.setter
    def backup_before_save(self, value):
        self.setValue("backup_before_save", value)

    @property
    def backup_before_downloading(self):
        return self.value("backup_before_downloading", True, bool)

    @backup_before_downloading.setter
    def backup_before_downloading(self, value):
        self.setValue("backup_before_downloading", value)

    # *********************** View ************************ #

    @property
    def alternate_layout(self):
        return self.value("alternate_layout", IS_DARWIN, bool)

    @alternate_layout.setter
    def alternate_layout(self, value):
        self.setValue("alternate_layout", value)

    @property
    def show_bouquets(self):
        return self.value("show_bouquets", True, bool)

    @show_bouquets.setter
    def show_bouquets(self, value):
        self.setValue("show_bouquets", value)

    @property
    def show_satellites(self):
        return self.value("show_satellites", True, bool)

    @show_satellites.setter
    def show_satellites(self, value):
        self.setValue("show_satellites", value)

    @property
    def show_picons(self):
        return self.value("show_picons", True, bool)

    @show_picons.setter
    def show_picons(self, value):
        self.setValue("show_picons", value)

    @property
    def show_epg(self):
        return self.value("show_epg", True, bool)

    @show_epg.setter
    def show_epg(self, value):
        self.setValue("show_epg", value)

    @property
    def show_timers(self):
        return self.value("show_timers", True, bool)

    @show_timers.setter
    def show_timers(self, value):
        self.setValue("show_timers", value)

    @property
    def show_control(self):
        return self.value("show_control", True, bool)

    @show_control.setter
    def show_control(self, value):
        self.setValue("show_control", value)

    # ******************** Local paths ******************** #

    @property
    def data_path(self):
        return self.value("data_path", self.Default.DATA_PATH.value)

    @data_path.setter
    def data_path(self, value):
        self.setValue("data_path", value)

    @property
    def picon_path(self):
        return self.value("picon_path", self.Default.PICON_PATH.value)

    @picon_path.setter
    def picon_path(self, value):
        self.setValue("picon_path", value)

    @property
    def backup_path(self):
        return self.value("backup_path", self.Default.BACKUP_PATH.value)

    @backup_path.setter
    def backup_path(self, value):
        self.setValue("backup_path", value)

    # ******************** Network ******************** #

    @property
    def box_services_path(self):
        return self.Default.BOX_SERVICES_PATH.value

    @property
    def box_satellite_path(self):
        return self.Default.BOX_SATELLITE_PATH.value

    @property
    def profiles(self):
        self.beginGroup("profiles")
        prs = self.childKeys()
        profiles = OrderedDict()
        if not prs:
            profiles[self.Default.PROFILE_NAME.value] = deepcopy(self.Default.PROFILE.value)
        else:
            for p in prs:
                profiles[p] = self.value(p, type=dict)
        self.endGroup()

        return profiles

    @profiles.setter
    def profiles(self, prs):
        self.remove("profiles")
        self.beginGroup("profiles")
        for n, p in prs.items():
            self.setValue(n, p)
        self.endGroup()

    @property
    def current_profile(self):
        return self._current_profile

    @current_profile.setter
    def current_profile(self, value):
        self._current_profile = value

    @property
    def picon_paths(self):
        paths = []
        for i in range(self.beginReadArray("picon_paths")):
            self.setArrayIndex(i)
            paths.append(self.value("path"))
        self.endArray()

        return paths or self.Default.PICON_PATHS.value

    @picon_paths.setter
    def picon_paths(self, paths):
        self.remove("picon_paths")
        self.beginWriteArray("picon_paths")
        for i, v in enumerate(paths):
            self.setArrayIndex(i)
            self.setValue("path", v)
        self.endArray()

    # ******************** Streams ******************** #

    @property
    def stream_lib(self):
        return self.value("stream_lib", self.Default.STREAM_LIB.value)

    @stream_lib.setter
    def stream_lib(self, value):
        self.setValue("stream_lib", value)


class SettingsDialog(QDialog):
    test = pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(f"{UI_PATH}settings.ui", self)

        self.settings = Settings()
        self._profiles = None
        self._current_profile = None

        self.init_ui()
        self.retranslate_ui()
        self.init_actions()
        self.init_settings()

        self.exec()

    def init_ui(self):
        self.test_network_box.setVisible(False)
        # Validators.
        self.ftp_port_edit.setValidator(QIntValidator(self.ftp_port_edit))
        self.http_port_edit.setValidator(QIntValidator(self.http_port_edit))
        self.telnet_port_edit.setValidator(QIntValidator(self.telnet_port_edit))
        # Setting model to profile view.
        self.profile_view.setModel(QStringListModel())
        # Streams.
        modes = (self.tr("Play"), self.tr("Zap"), self.tr("Zap and Play"), self.tr("Disabled"))
        self.play_streams_mode_combo_box.setModel(QStringListModel(modes))
        self.play_streams_mode_combo_box.setEnabled(False)
        self.stream_lib_combo_box.setModel(QStringListModel(("VLC", "MPV", "GStreamer")))

    def retranslate_ui(self):
        _translate = QCoreApplication.translate
        if not IS_LINUX:
            self.profile_add_button.setText(_translate("SettingsDialog", "Add"))
            self.profile_edit_button.setText(_translate("SettingsDialog", "Rename"))
            self.profile_remove_button.setText(_translate("SettingsDialog", "Remove"))
            self.add_picon_path_button.setText("+")
            self.remove_picon_path_button.setText("-")

    def init_actions(self):
        self.network_tool_button.toggled.connect(lambda s: self.stacked_widget.setCurrentIndex(0) if s else None)
        self.paths_tool_button.toggled.connect(lambda s: self.stacked_widget.setCurrentIndex(1) if s else None)
        self.program_tool_button.toggled.connect(lambda s: self.stacked_widget.setCurrentIndex(2) if s else None)
        # Profile
        self.profile_add_button.clicked.connect(self.on_profile_add)
        self.profile_edit_button.clicked.connect(self.on_profile_edit)
        self.profile_remove_button.clicked.connect(self.on_profile_remove)
        profile_model = self.profile_view.model()
        profile_model.dataChanged.connect(self.on_prfile_name_changed)
        profile_model.rowsRemoved.connect(self.on_profiles_changed)
        self.profile_view.selectionModel().currentChanged.connect(self.on_profile_selection)
        self.login_edit.editingFinished.connect(lambda: self.on_profile_params_set("user", self.login_edit))
        self.password_edit.editingFinished.connect(
            lambda: self.on_profile_params_set("password", self.password_edit))
        self.host_edit.editingFinished.connect(lambda: self.on_profile_params_set("host", self.host_edit))
        self.ftp_port_edit.editingFinished.connect(
            lambda: self.on_profile_params_set("ftp_port", self.ftp_port_edit))
        self.http_port_edit.editingFinished.connect(
            lambda: self.on_profile_params_set("http_port", self.http_port_edit))
        self.telnet_port_edit.editingFinished.connect(
            lambda: self.on_profile_params_set("ftp_port", self.telnet_port_edit))
        self.picon_path_box.activated.connect(
            lambda i: self._current_profile.update({"box_picon_path": self.picon_path_box.currentText()}))
        self.http_ssl_check_box.toggled.connect(self.on_http_ssl_toggled)
        self.add_picon_path_button.clicked.connect(self.on_picon_path_add)
        self.remove_picon_path_button.clicked.connect(self.on_picon_path_remove)
        picon_paths_model = self.picon_path_box.model()
        picon_paths_model.rowsRemoved.connect(self.on_picon_paths_changed)
        picon_paths_model.rowsInserted.connect(self.on_picon_paths_changed)
        # Network testing
        self.test_button.clicked.connect(lambda: self.test.emit(True))
        self.close_test_button.clicked.connect(lambda: self.test.emit(False))
        self.test.connect(self.test_network_box.setVisible)
        self.test.connect(self.test_button.setHidden)
        self.test.connect(self.profile_buttons_frame.setHidden)
        self.test.connect(self.profile_view.setDisabled)
        self.test.connect(self.on_test_connection)
        # Paths
        self.browse_data_path_button.clicked.connect(lambda b: self.on_path_set(self.data_path_edit))
        self.browse_picon_path_button.clicked.connect(lambda b: self.on_path_set(self.picon_path_edit))
        self.browse_backup_path_button.clicked.connect(lambda b: self.on_path_set(self.backup_path_edit))
        # Dialog buttons
        self.action_button_box.clicked.connect(self.on_accept)

    def init_settings(self):
        # Profiles
        self._profiles = self.settings.profiles
        self.profile_view.model().setStringList(self._profiles)
        self.profile_view.setCurrentIndex(self.profile_view.model().createIndex(0, 0))
        self.on_profiles_changed()
        #  Init picon paths for the box.
        self.picon_path_box.model().clear()
        self.picon_path_box.addItems(self.settings.picon_paths)
        self.picon_path_box.setCurrentText(self._current_profile.get("box_picon_path"))
        # Paths
        self.data_path_edit.setText(self.settings.data_path)
        self.picon_path_edit.setText(self.settings.picon_path)
        self.backup_path_edit.setText(self.settings.backup_path)
        # Program
        self.load_last_config_check_box.setChecked(self.settings.load_last_config)
        self.show_services_hints_check_box.setChecked(self.settings.show_srv_hints)
        self.show_fav_hints_check_box.setChecked(self.settings.show_fav_hints)
        self.backup_befor_save_check_box.setChecked(self.settings.backup_before_save)
        self.backup_befor_download_check_box.setChecked(self.settings.backup_before_downloading)
        self.stream_lib_combo_box.setCurrentText(self.settings.stream_lib)

    def settings_save(self):
        # Profiles
        self.settings.profiles = self._profiles
        # Paths
        p_model = self.picon_path_box.model()
        p_paths = [p_model.index(r, 0).data() for r in range(p_model.rowCount())]
        self.settings.picon_paths = p_paths
        self.settings.data_path = self.data_path_edit.text()
        self.settings.picon_path = self.picon_path_edit.text()
        self.settings.backup_path = self.backup_path_edit.text()
        # Program
        self.settings.load_last_config = self.load_last_config_check_box.isChecked()
        self.settings.show_srv_hints = self.show_services_hints_check_box.isChecked()
        self.settings.show_fav_hints = self.show_fav_hints_check_box.isChecked()
        self.settings.backup_before_save = self.backup_befor_save_check_box.isChecked()
        self.settings.backup_before_downloading = self.backup_befor_download_check_box.isChecked()
        self.settings.stream_lib = self.stream_lib_combo_box.currentText()

    # ******************** Network ******************** #

    def on_profile_add(self, state):
        count = 0
        name = "profile"
        while name in self._profiles:
            count += 1
            name = f"profile{count}"

        p_data = deepcopy(self.settings.Default.PROFILE.value)
        p_data["name"] = name
        self._profiles[name] = p_data
        model = self.profile_view.model()
        model.setStringList(self._profiles)
        self.profile_view.setCurrentIndex(model.index(model.rowCount() - 1))
        self.on_profiles_changed()

    def on_profile_edit(self, state):
        indexes = self.profile_view.selectionModel().selectedIndexes()
        if not indexes:
            return

        if len(indexes) > 1:
            QMessageBox.critical(self, APP_NAME, self.tr("Please, select only one item!"))
            return

        self.profile_view.edit(indexes[0])

    def on_prfile_name_changed(self, top, bottom):
        prev_name = self._current_profile["name"]
        cur_name = top.data()
        if cur_name == prev_name:
            return

        if not cur_name:
            QMessageBox.critical(self, APP_NAME, self.tr("The name can't be empty!"))
            top.model().setData(top, prev_name)
            return

        profile = self._profiles.pop(prev_name, None)
        if profile:
            self._current_profile["name"] = cur_name
            self._profiles[cur_name] = profile

    def on_profile_remove(self, state):
        if QMessageBox.question(self, APP_NAME, self.tr("Are you sure?")) != QMessageBox.Yes:
            return

        model = self.profile_view.model()
        for i in self.profile_view.selectionModel().selectedIndexes():
            if self._profiles.pop(i.data(), None):
                model.removeRow(i.row())

    def on_profile_selection(self, index):
        profile = self._profiles.get(index.data(), None)
        if profile:
            self._current_profile = profile
            self.login_edit.setText(profile.get("user", Settings.Default.USER.value))
            self.password_edit.setText(profile.get("password", Settings.Default.PASSWORD.value))
            self.host_edit.setText(profile.get("host", Settings.Default.HOST.value))
            self.ftp_port_edit.setText(profile.get("ftp_port", Settings.Default.FTP_PORT.value))
            self.http_port_edit.setText(profile.get("http_port", Settings.Default.HTTP_PORT.value))
            self.telnet_port_edit.setText(profile.get("telnet_port", Settings.Default.TELNET_PORT.value))
            self.picon_path_box.setCurrentText(profile.get("box_picon_path", Settings.Default.BOX_PICON_PATH.value))
            self.http_ssl_check_box.setChecked(profile.get("http_use_ssl", Settings.Default.HTTP_USE_SSL.value))
        else:
            QMessageBox.critical(self, APP_NAME, self.tr("Profile loading error!"))

    def on_test_connection(self, state):
        if state:
            QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_profile_params_set(self, param, edit):
        """ Sets the current profile parameter when editing the value is finished [editingFinished event].

            @param param: the name of profile parameter.
            @param edit: QLineEdit object for the given parameter.
         """
        self._current_profile[param] = edit.text()

    def on_http_ssl_toggled(self, checked):
        self._current_profile["http_use_ssl"] = checked
        port = "443" if checked else Settings.Default.HTTP_PORT.value
        self.http_port_edit.setText(port)
        self._current_profile["http_port"] = port

    def on_profiles_changed(self):
        self.profile_remove_button.setEnabled(self.profile_view.model().rowCount() > 1)

    # ******************** Paths ******************** #

    def on_picon_path_add(self, state=False):
        dialog = InputDialog("E2Toolkit [New path to picons]", "Path:", parent=self)
        if not dialog.exec():
            return

        path = dialog.textValue()
        path = path if path.endswith("/") else f"{path}/"
        path = path if path.startswith("/") else f"/{path}"
        model = self.picon_path_box.model()
        if path in {model.index(r, 0).data() for r in range(model.rowCount())}:
            QMessageBox.critical(self, APP_NAME, self.tr("This path already exist!"))
            return

        self.picon_path_box.insertItem(self.picon_path_box.count() + 1, path)
        self.picon_path_box.setCurrentText(path)

    def on_picon_path_remove(self):
        self.picon_path_box.removeItem(self.picon_path_box.currentIndex())

    def on_path_set(self, edit):
        """ Sets path to the given edit field. """
        path = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"), edit.text())
        if path:
            edit.setText(path + os.sep)

    def on_picon_paths_changed(self):
        self.remove_picon_path_button.setEnabled(self.picon_path_box.count() > 1)

    # ******************** Dialog buttons. ******************** #

    def on_accept(self, button):
        role = self.action_button_box.buttonRole(button)
        if role == QDialogButtonBox.AcceptRole:
            if QMessageBox.question(self, APP_NAME, self.tr("Are you sure?")) == QMessageBox.Yes:
                self.settings_save()
                self.accept()
        elif role == QDialogButtonBox.ResetRole:
            self.reset_settings_to_defaults()
        else:
            self.reject()

    def reset_settings_to_defaults(self):
        msg = "{}<p align='center'>{}<br>".format(
            self.tr("This operation resets all settings to the defaults."),
            self.tr("Are you sure?"))
        if QMessageBox.question(self, APP_NAME, msg) == QDialogButtonBox.Yes:
            self.settings.clear()
            self.init_settings()
            self.settings_save()


if __name__ == "__main__":
    pass
