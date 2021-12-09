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
from enum import Enum
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QSettings, QSize, QStringListModel
from PyQt5.QtWidgets import QDialog, QMessageBox, QDialogButtonBox, QFileDialog

from app.commons import APP_NAME

IS_DARWIN = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"
IS_LINUX = sys.platform == "linux"

# Base UI files path.
UI_PATH = "app/ui/res/"


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

        DEFAULT_FROFILE_NAME = "Default"
        DEFAULT_PROFILE = {"name": DEFAULT_FROFILE_NAME,
                           "user": USER,
                           "password": PASSWORD,
                           "host": HOST,
                           "ftp_port": FTP_PORT,
                           "http_port": HTTP_PORT,
                           "telnet_port": TELNET_PORT,
                           "http_use_ssl": HTTP_USE_SSL,
                           "box_picon_path": BOX_PICON_PATH}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_profile = self.Default.DEFAULT_PROFILE.value

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
        if not prs:
            self.endGroup()
            return [self.Default.DEFAULT_PROFILE.value]

        prs = [self.value(p) for p in prs]
        self.endGroup()

        return prs

    @profiles.setter
    def profiles(self, prs):
        self.beginGroup("profiles")
        for p in prs:
            self.setValue(p["name"], p)
        self.endGroup()

    @property
    def current_profile(self):
        return self._current_profile

    @current_profile.setter
    def current_profile(self, value):
        self._current_profile = value

    # ******************** Streams ******************** #

    @property
    def stream_lib(self):
        return self.value("stream_lib", self.Default.STREAM_LIB.value)

    @stream_lib.setter
    def stream_lib(self, value):
        self.setValue("stream_lib", value)


class SettingsDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(f"{UI_PATH}settings.ui", self)

        self.settings = Settings()
        self._profiles = OrderedDict()
        self._current_profile = None

        self.init_ui()
        self.init_actions()
        self.init_settings()

        self.exec_()

    def init_ui(self):
        # Setting model to profiles view.
        self.profile_view.setModel(QStringListModel())
        # Init picon paths for the box.
        self.picon_path_box.addItems(("/usr/share/enigma2/picon/", "/media/hdd/picon/", "/media/usb/picon/",
                                      "/media/mmc/picon/", "/media/cf/picon/"))
        # Streams.
        modes = (self.tr("Play"), self.tr("Zap"), self.tr("Zap and Play"), self.tr("Disabled"))
        self.play_streams_mode_combo_box.setModel(QStringListModel(modes))
        self.play_streams_mode_combo_box.setEnabled(False)
        self.stream_lib_combo_box.setModel(QStringListModel(("VLC", "MPV", "GStreamer")))

    def init_actions(self):
        self.network_tool_button.toggled.connect(lambda s: self.stacked_widget.setCurrentIndex(0) if s else None)
        self.paths_tool_button.toggled.connect(lambda s: self.stacked_widget.setCurrentIndex(1) if s else None)
        self.program_tool_button.toggled.connect(lambda s: self.stacked_widget.setCurrentIndex(2) if s else None)
        # Profile
        self.profile_add_button.clicked.connect(self.on_profile_add)
        self.profile_edit_button.clicked.connect(self.on_profile_edit)
        self.profile_remove_button.clicked.connect(self.on_profile_remove)
        self.test_button.clicked.connect(self.on_test_connection)
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
        # Paths
        self.browse_data_path_button.clicked.connect(lambda b: self.on_path_set(self.data_path_edit))
        self.browse_picon_path_button.clicked.connect(lambda b: self.on_path_set(self.picon_path_edit))
        self.browse_backup_path_button.clicked.connect(lambda b: self.on_path_set(self.backup_path_edit))
        # Dialog buttons
        self.action_button_box.clicked.connect(self.on_accept)

    def init_settings(self):
        # Profiles
        for p in self.settings.profiles:
            self._profiles[p.get("name")] = p
        self.profile_view.model().setStringList(self._profiles)
        self.profile_view.setCurrentIndex(self.profile_view.model().createIndex(0, 0))
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
        self.settings.profiles = self._profiles.values()
        # Paths
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
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_profile_edit(self, state):
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_profile_remove(self, state):
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

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

    # ******************** Paths ******************** #

    def on_path_set(self, edit):
        """ Sets path to the given edit field. """
        path = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"), edit.text())
        if path:
            edit.setText(path + os.sep)

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
