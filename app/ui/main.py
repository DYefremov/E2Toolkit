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


""" Main UI module. """
import sys
from enum import IntEnum
from pathlib import Path

from PyQt5.QtCore import QTranslator
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QActionGroup, QAction, QMessageBox, QFileDialog

from app.commons import APP_VERSION, APP_NAME, LANG_PATH, LOCALES
from app.ui.settings import SettingsDialog, Settings
from .ui import Ui_MainWindow


class Application(QApplication):
    def __init__(self, argv: sys.argv):
        super(Application, self).__init__(argv)
        self.setWindowIcon(QIcon.fromTheme("applications-utilities"))
        self.setApplicationVersion(APP_VERSION)
        self.setApplicationName(APP_NAME)
        self.setOrganizationDomain(APP_NAME)

        self.settings = Settings()
        self.translator = QTranslator(self)

    @staticmethod
    def run():
        app = Application(sys.argv)
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec())

    def set_locale(self, locale):
        if self.translator.load("{}e2toolkit.{}.qm".format(LANG_PATH, locale)):
            self.installTranslator(self.translator)
        else:
            self.removeTranslator(self.translator)

        self.settings.app_locale = locale


class MainWindow(QMainWindow):
    """ The main UI class. """

    class Page(IntEnum):
        """ Main stack widget page. """
        BOUQUETS = 0
        SAT = 1
        PICONS = 2
        TV = 3
        EPG = 4
        TIMER = 5
        FTP = 6
        LOGO = 7

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.settings = Settings()

        self.init_ui()
        self.init_actions()
        self.init_language()

    def init_ui(self):
        self.resize(self.settings.app_window_size)
        # Tool buttons
        self.ui.satellite_tool_button.setVisible(False)
        self.ui.picon_tool_button.setVisible(False)
        self.ui.timer_tool_button.setVisible(False)
        self.ui.ftp_tool_button.setVisible(False)
        self.ui.logo_tool_button.setVisible(False)

    def init_actions(self):
        # File menu
        self.ui.import_action.triggered.connect(self.on_data_import)
        self.ui.open_action.triggered.connect(self.on_data_open)
        self.ui.extract_action.triggered.connect(self.on_data_extract)
        self.ui.exit_action.triggered.connect(self.on_app_exit)
        # Settings
        self.ui.settings_action.triggered.connect(self.on_settings_dialog)
        # Toolbar
        self.ui.download_tool_button.clicked.connect(self.on_data_download)
        self.ui.upload_tool_button.clicked.connect(self.on_data_upload)
        self.ui.bouquet_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, self.Page.BOUQUETS))
        self.ui.satellite_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, self.Page.SAT))
        self.ui.picon_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, self.Page.PICONS))
        self.ui.tv_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, self.Page.TV))
        self.ui.epg_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, self.Page.EPG))
        self.ui.timer_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, self.Page.TIMER))
        self.ui.ftp_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, self.Page.FTP))
        self.ui.logo_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, self.Page.LOGO))
        # About
        self.ui.about_action.triggered.connect(self.on_about)

    def init_language(self):
        app_locale = self.settings.app_locale
        group = QActionGroup(self)

        for name, bcp in LOCALES:
            action = QAction(name, self.ui.language_menu)
            action.setCheckable(True)
            action.setData(bcp)
            if bcp == app_locale:
                action.setChecked(True)
                self.set_locale(bcp)
            self.ui.language_menu.addAction(action)
            group.addAction(action)

        group.triggered.connect(self.on_change_language)

    # ******************** Actions ******************** #

    def on_data_download(self):
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_data_upload(self):
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_data_import(self, state):
        resp = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"), str(Path.home()))
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_data_open(self, state):
        resp = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"), str(Path.home()))
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_data_extract(self, state):
        resp = QFileDialog.getOpenFileNames(self, self.tr("Select Archive"), str(Path.home()),
                                            "Archive files (*.gz *.zip)")
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_app_exit(self, state):
        self.close()

    def on_settings_dialog(self, state):
        SettingsDialog()

    def on_change_language(self, action):
        self.set_locale(action.data() or "")

    def set_locale(self, locale):
        app = Application.instance()
        app.set_locale(locale)
        self.ui.retranslateUi(self)

    def on_stack_page_changed(self, state, p_num):
        self.ui.stacked_widget.setCurrentIndex(p_num) if state else None
        self.ui.fav_splitter.setVisible(p_num not in (self.Page.SAT, self.Page.FTP, self.Page.LOGO, self.Page.TIMER))

    def on_about(self, state):
        lic = self.tr("This program comes with absolutely no warranty.<br/>See the <a href=\"{}\">{}</a> for details.")
        lic = lic.format("http://www.gnu.org/licenses/gpl-3.0.html",
                         self.tr("GNU General Public License, version 3 or later"))
        msg = """<h2>{}</h2>
               <h4>{}</h4>
               Copyright &copy; 2021 Dmitriy Yefremov<br/><br/>
               {}
               """.format(APP_NAME, APP_VERSION, lic)

        QMessageBox.about(self, APP_NAME, msg)

    def closeEvent(self, event):
        """ Main window close event. """
        self.settings.app_window_size = self.size()


if __name__ == "__main__":
    pass
