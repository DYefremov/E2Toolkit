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
from collections import OrderedDict
from enum import Enum
from pathlib import Path

from PyQt5.QtCore import QSettings, QSize, QStringListModel
from PyQt5.QtWidgets import QDialog, QMessageBox, QDialogButtonBox, QFileDialog

from app.commons import APP_NAME
from app.ui.settings_ui import Ui_SettingsDialog


class Settings(QSettings):
    """ Base settings class. """

    class Default(Enum):
        """ Default settings """
        HOME_PATH = str(Path.home())
        DATA_PATH = HOME_PATH + "/{}/data/".format(APP_NAME)
        BACKUP_PATH = DATA_PATH + "backup/"
        PICON_PATH = DATA_PATH + "picons/"
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
        return self.value("load_last_config", False)

    @load_last_config.setter
    def load_last_config(self, value):
        self.setValue("load_last_config", value)

    @property
    def last_config(self):
        return self.value("last_config", {}, dict)

    @last_config.setter
    def last_config(self, value):
        self.setValue("last_config", value)

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
    def __init__(self):
        super(SettingsDialog, self).__init__()
        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)

        self.settings = Settings()
        self._profiles = OrderedDict()
        self._current_profile = None

        self.init_ui()
        self.init_actions()
        self.init_settings()

        self.exec_()

    def init_ui(self):
        # Setting model to profiles view.
        self.ui.profile_view.setModel(QStringListModel())
        # Init picon paths for the box
        self.ui.picon_path_box.addItems(("/usr/share/enigma2/picon/", "/media/hdd/picon/", "/media/usb/picon/",
                                         "/media/mmc/picon/", "/media/cf/picon/"))
        # Streams.
        modes = (self.tr("Play"), self.tr("Zap"), self.tr("Zap and Play"), self.tr("Disabled"))
        self.ui.play_streams_mode_combo_box.setModel(QStringListModel(modes))
        self.ui.play_streams_mode_combo_box.setEnabled(False)
        self.ui.stream_lib_combo_box.setModel(QStringListModel(("VLC", "MPV", "GStreamer")))

    def init_actions(self):
        self.ui.network_tool_button.toggled.connect(lambda s: self.ui.stacked_widget.setCurrentIndex(0) if s else None)
        self.ui.paths_tool_button.toggled.connect(lambda s: self.ui.stacked_widget.setCurrentIndex(1) if s else None)
        self.ui.program_tool_button.toggled.connect(lambda s: self.ui.stacked_widget.setCurrentIndex(2) if s else None)
        # Profile
        self.ui.profile_add_button.clicked.connect(self.on_profile_add)
        self.ui.profile_edit_button.clicked.connect(self.on_profile_edit)
        self.ui.profile_remove_button.clicked.connect(self.on_profile_remove)
        self.ui.test_button.clicked.connect(self.on_test_connection)
        self.ui.profile_view.selectionModel().currentChanged.connect(self.on_profile_selection)
        self.ui.login_edit.editingFinished.connect(lambda: self.on_profile_params_set("user", self.ui.login_edit))
        self.ui.password_edit.editingFinished.connect(
            lambda: self.on_profile_params_set("password", self.ui.password_edit))
        self.ui.host_edit.editingFinished.connect(lambda: self.on_profile_params_set("host", self.ui.host_edit))
        self.ui.ftp_port_edit.editingFinished.connect(
            lambda: self.on_profile_params_set("ftp_port", self.ui.ftp_port_edit))
        self.ui.http_port_edit.editingFinished.connect(
            lambda: self.on_profile_params_set("http_port", self.ui.http_port_edit))
        self.ui.telnet_port_edit.editingFinished.connect(
            lambda: self.on_profile_params_set("ftp_port", self.ui.telnet_port_edit))
        self.ui.picon_path_box.activated.connect(
            lambda i: self._current_profile.update({"box_picon_path": self.ui.picon_path_box.currentText()}))
        self.ui.http_ssl_check_box.toggled.connect(self.on_http_ssl_toggled)
        # Paths
        self.ui.browse_data_path_button.clicked.connect(lambda b: self.on_path_set(self.ui.data_path_edit))
        self.ui.browse_picon_path_button.clicked.connect(lambda b: self.on_path_set(self.ui.picon_path_edit))
        self.ui.browse_backup_path_button.clicked.connect(lambda b: self.on_path_set(self.ui.backup_path_edit))
        # Dialog buttons
        self.ui.action_button_box.clicked.connect(self.on_accept)

    def init_settings(self):
        # Profiles
        for p in self.settings.profiles:
            self._profiles[p.get("name")] = p
        self.ui.profile_view.model().setStringList(self._profiles)
        self.ui.profile_view.setCurrentIndex(self.ui.profile_view.model().createIndex(0, 0))
        # Paths
        self.ui.data_path_edit.setText(self.settings.data_path)
        self.ui.picon_path_edit.setText(self.settings.picon_path)
        self.ui.backup_path_edit.setText(self.settings.backup_path)
        # Program
        self.ui.stream_lib_combo_box.setCurrentText(self.settings.stream_lib)

    def settings_save(self):
        # Profiles
        self.settings.profiles = self._profiles.values()
        # Paths
        self.settings.data_path = self.ui.data_path_edit.text()
        self.settings.picon_path = self.ui.picon_path_edit.text()
        self.settings.backup_path = self.ui.backup_path_edit.text()
        # Program
        self.settings.stream_lib = self.ui.stream_lib_combo_box.currentText()

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
            self.ui.login_edit.setText(profile.get("user", Settings.Default.USER.value))
            self.ui.password_edit.setText(profile.get("password", Settings.Default.PASSWORD.value))
            self.ui.host_edit.setText(profile.get("host", Settings.Default.HOST.value))
            self.ui.ftp_port_edit.setText(profile.get("ftp_port", Settings.Default.FTP_PORT.value))
            self.ui.http_port_edit.setText(profile.get("http_port", Settings.Default.HTTP_PORT.value))
            self.ui.telnet_port_edit.setText(profile.get("telnet_port", Settings.Default.TELNET_PORT.value))
            self.ui.picon_path_box.setCurrentText(profile.get("box_picon_path", Settings.Default.BOX_PICON_PATH.value))
            self.ui.http_ssl_check_box.setChecked(profile.get("http_use_ssl", Settings.Default.HTTP_USE_SSL.value))
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
        self.ui.http_port_edit.setText(port)
        self._current_profile["http_port"] = port

    # ******************** Paths ******************** #

    def on_path_set(self, edit):
        """ Sets path to the given edit field. """
        path = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"), edit.text())
        if path:
            edit.setText(path + os.sep)

    # ******************** Dialog buttons. ******************** #

    def on_accept(self, button):
        role = self.ui.action_button_box.buttonRole(button)
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
