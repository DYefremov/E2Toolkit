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
from collections import OrderedDict
from enum import Enum
from pathlib import Path

from PyQt5.QtCore import QSettings, QSize, QStringListModel
from PyQt5.QtWidgets import QDialog, QMessageBox, QDialogButtonBox

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

        USER = "root"
        PASSWORD = ""
        HOST = "127.0.0.1"
        FTP_PORT = 21
        HTTP_PORT = 80
        TELNET_PORT = 23
        HTTP_USE_SSL = False

        APP_WINDOW_SIZE = QSize(850, 560)
        APP_LOCALE = "en"
        STREAM_LIB = "vlc"

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


class SettingsDialog(QDialog):
    def __init__(self):
        super(SettingsDialog, self).__init__()
        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)
        self.settings = Settings()

        self.init_ui()
        self.init_actions()

        self._profiles = OrderedDict()
        self.init_settings()

        self.exec_()

    def init_ui(self):
        self.ui.program_tool_button.setEnabled(False)
        # Setting model to profiles view.
        self.ui.profile_view.setModel(QStringListModel())
        # Init picon paths for the box
        self.ui.picon_path_box.addItems(("/usr/share/enigma2/picon/", "/media/hdd/picon", "/media/usb/picon",
                                         "/media/mmc/picon", "/media/cf/picon"))

    def init_actions(self):
        self.ui.network_tool_button.toggled.connect(lambda s: self.ui.stacked_widget.setCurrentIndex(0) if s else None)
        self.ui.paths_tool_button.toggled.connect(lambda s: self.ui.stacked_widget.setCurrentIndex(1) if s else None)
        self.ui.program_tool_button.toggled.connect(lambda s: self.ui.stacked_widget.setCurrentIndex(2) if s else None)
        # Profile
        self.ui.profile_add_button.clicked.connect(self.on_profile_add)
        self.ui.profile_edit_button.clicked.connect(self.on_profile_edit)
        self.ui.profile_remove_button.clicked.connect(self.on_profile_remove)
        self.ui.test_button.clicked.connect(self.on_test_connection)
        self.ui.profile_view.clicked.connect(self.on_profile_selection)
        # Dialog buttons
        self.ui.action_button_box.clicked.connect(self.on_accept)

    def init_settings(self):
        # Profiles
        for p in self.settings.profiles:
            self._profiles[p.get("name")] = p
        self.ui.profile_view.model().setStringList(self._profiles)
        # Paths
        self.ui.local_data_path_edit.setText(self.settings.data_path)
        self.ui.local_picon_path_edit.setText(self.settings.picon_path)
        self.ui.local_backup_path_edit.setText(self.settings.backup_path)

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
            self.ui.login_edit.setText(profile.get("user", Settings.Default.USER.value))
            self.ui.password_edit.setText(profile.get("password", Settings.Default.PASSWORD.value))
            self.ui.host_edit.setText(profile.get("host", Settings.Default.HOST.value))
            self.ui.ftp_port_edit.setText(str(profile.get("ftp_port", Settings.Default.FTP_PORT.value)))
            self.ui.http_port_edit.setText(str(profile.get("http_port", Settings.Default.HTTP_PORT.value)))
            self.ui.telnet_port_edit.setText(str(profile.get("telnet_port", Settings.Default.TELNET_PORT.value)))
        else:
            QMessageBox.critical(self, APP_NAME, self.tr("Profile loading error!"))

    def on_test_connection(self, state):
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    # ******************** Dialog buttons. ******************** #

    def on_accept(self, button):
        role = self.ui.action_button_box.buttonRole(button)
        if role == QDialogButtonBox.YesRole:
            if QMessageBox.question(self, APP_NAME, self.tr("Are you sure?")) == QMessageBox.Yes:
                self.accept()
        elif role == QDialogButtonBox.ResetRole:
            QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))
        else:
            self.reject()


if __name__ == "__main__":
    pass
