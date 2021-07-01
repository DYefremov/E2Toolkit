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
import os
import sys
from collections import OrderedDict, Counter
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QTranslator, QStringListModel, QTimer, pyqtSlot, Qt
from PyQt5.QtGui import QIcon, QStandardItem
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog, QActionGroup, QAction

from app.commons import APP_VERSION, APP_NAME, LANG_PATH, log, LOCALES
from app.connections import HttpAPI, download_data, DownloadType
from app.enigma.bouquets import BouquetsReader
from app.enigma.ecommons import BqServiceType, Service
from app.enigma.lamedb import get_services
from app.satellites.satxml import get_satellites
from app.ui.settings import SettingsDialog, Settings
from app.ui.uicommons import Column, IPTV_ICON, LOCKED_ICON
from .ui import MainUiWindow, Page


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


class MainWindow(MainUiWindow):
    """ The main UI class. """

    def __init__(self):
        super(MainWindow, self).__init__()
        # Settings.
        self.settings = Settings()
        self._profiles = OrderedDict()
        # Cached data.
        self._bouquets = {}
        self._bq_file = {}
        self._extra_bouquets = {}
        self._services = {}
        self._blacklist = set()
        self._alt_file = set()
        self._picons = {}
        self._marker_types = {BqServiceType.MARKER.name,
                              BqServiceType.SPACE.name,
                              BqServiceType.ALT.name}
        # HTTP API.
        self._update_state_timer = QTimer(self)
        self._http_api = None
        # Streams.
        self._player = None
        # Initialization.
        self.init_ui()
        self.init_actions()
        self.init_language()
        self.init_profiles()
        self.init_http_api()

    def init_ui(self):
        self.resize(self.settings.app_window_size)

    def init_actions(self):
        # File menu.
        self.import_action.triggered.connect(self.on_data_import)
        self.open_action.triggered.connect(self.on_data_open)
        self.extract_action.triggered.connect(self.on_data_extract)
        self.exit_action.triggered.connect(self.on_app_exit)
        # Settings.
        self.settings_action.triggered.connect(self.on_settings_dialog)
        # Toolbar.
        self.download_tool_button.clicked.connect(self.on_data_download)
        self.upload_tool_button.clicked.connect(self.on_data_upload)
        # Models and Views.
        self.bouquets_view.selectionModel().selectionChanged.connect(self.on_bouquet_selection)
        self.fav_view.selectionModel().selectionChanged.connect(self.on_fav_selection)
        # Streams.
        self.media_play_tool_button.clicked.connect(self.playback_start)
        self.media_stop_tool_button.clicked.connect(self.playback_stop)
        self.media_full_tool_button.clicked.connect(self.show_full_screen)
        self.fav_view.mouseDoubleClickEvent = self.playback_start
        self.media_widget.mouseDoubleClickEvent = self.show_full_screen
        # HTTP API.
        self._update_state_timer.timeout.connect(self.update_state)
        # About.
        self.about_action.triggered.connect(self.on_about)

    def init_language(self):
        app_locale = self.settings.app_locale
        group = QActionGroup(self)

        for name, bcp in LOCALES:
            action = QAction(name, self.language_menu)
            action.setCheckable(True)
            action.setData(bcp)
            if bcp == app_locale:
                action.setChecked(True)
                self.set_locale(bcp)
            self.language_menu.addAction(action)
            group.addAction(action)

        group.triggered.connect(lambda a: self.set_locale(a.data() or ""))

    def init_profiles(self):
        for p in self.settings.profiles:
            self._profiles[p.get("name")] = p
        self.profile_combo_box.setModel(QStringListModel(list(self._profiles)))
        self.settings.current_profile = self._profiles[self.profile_combo_box.currentText()]

    def init_http_api(self):
        if self._http_api:
            self._update_state_timer.stop()

        callbacks = {HttpAPI.Request.INFO: self.update_state_info,
                     HttpAPI.Request.STREAM: self.update_playback,
                     HttpAPI.Request.TIMER_LIST: self.update_timer_list,
                     HttpAPI.Request.EPG: self.update_single_epg}
        self._http_api = HttpAPI(self._profiles.get(self.profile_combo_box.currentText()), callbacks)
        self._update_state_timer.start(3000)

    # ******************** Actions ******************** #

    def on_data_download(self):
        try:
            self.log_text_browser.clear()
            page = Page(self.stacked_widget.currentIndex())
            download_type = DownloadType.ALL
            if page is Page.SAT:
                download_type = DownloadType.SATELLITES

            download_data(settings=self.settings,
                          download_type=download_type,
                          callback=self.log_text_browser.append)
        except Exception as e:
            log(e)
            self.log_text_browser.append("Error: {}".format(str(e)))
            self.status_bar.showMessage("Error: {}".format(str(e)))
        else:
            if page is Page.SAT:
                self.load_satellites(self.get_data_path() + "satellites.xml")
            else:
                self.load_data()

    def on_data_upload(self):
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_data_import(self, state):
        resp = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"), str(Path.home()))
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_data_open(self, state):
        page = Page(self.stacked_widget.currentIndex())
        if page is Page.BOUQUETS:
            resp = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"), str(Path.home()))
            if resp:
                self.load_data(resp + os.sep)
        elif page is Page.SAT:
            resp = QFileDialog.getOpenFileName(self, self.tr("Select file"), str(Path.home()), " satellites.xml")
            if resp[0]:
                self.load_satellites(resp[0])
        elif page is Page.PICONS:
            resp = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"), str(Path.home()))
            if resp:
                self.load_data(resp + os.sep)
        else:
            QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_data_extract(self, state):
        resp = QFileDialog.getOpenFileNames(self, self.tr("Select Archive"), str(Path.home()),
                                            "Archive files (*.gz *.zip)")
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_settings_dialog(self, state):
        SettingsDialog()
        self.init_profiles()

    def set_locale(self, locale):
        app = Application.instance()
        app.set_locale(locale)
        self.retranslate_ui(self)

    def on_bouquet_selection(self, selected_item, deselected_item):
        indexes = selected_item.indexes()
        if len(indexes) > 1:
            bq_selected = "{}:{}".format(indexes[Column.BQ_NAME].data(), indexes[Column.BQ_TYPE].data())
            self.update_bouquet_services(bq_selected)

    def on_fav_selection(self, selected_item, deselected_item):
        if self.current_page is Page.EPG and self._http_api:
            ind = selected_item.indexes()
            if len(ind) == 8:
                ref = self.get_service_ref(ind[Column.FAV_ID].data(), ind[Column.FAV_TYPE].data())
                self._http_api.send(self._http_api.Request.EPG, ref)

    def closeEvent(self, event):
        """ Main window close event. """
        self.settings.app_window_size = self.size()

    # ******************** Data loading. ******************** #

    def get_data_path(self):
        profile = self._profiles.get(self.profile_combo_box.currentText())
        return "{}{}{}".format(self.settings.data_path, profile["name"], os.sep)

    def load_data(self, path=None):
        if not path:
            path = self.get_data_path()

        try:
            self.clean_data()
            bouquets = BouquetsReader(path).get()
            services = get_services(path)
        except FileNotFoundError as e:
            msg = self.tr("Please, download files from receiver or setup your path for read data!")
            QMessageBox.critical(self, APP_NAME, msg)
            log(e)
        else:
            self.append_data(bouquets, services)

    def append_data(self, bouquets, services):
        self.append_bouquets(bouquets)
        self.append_services(services)

    def append_services(self, services):
        model = self.services_view.model()
        for s in services:
            self._services[s.fav_id] = s
            model.appendRow((QStandardItem(i) for i in s))

        self.set_services_headers()
        # Counting by type of service.
        counter = Counter(s.service_type for s in services)
        self.data_count_label.setText(str(counter.get("Data")))
        self.radio_count_label.setText(str(counter.get("Radio")))
        self.tv_count_label.setText(str(sum(v for k, v in counter.items() if k not in {"Data", "Radio"})))

    def append_bouquets(self, bouquets):
        model = self.bouquets_view.model()
        root_node = model.invisibleRootItem()
        for i, bqs in enumerate(bouquets):
            root = QStandardItem(QIcon.fromTheme("tv-symbolic" if i == 0 else "radio-symbolic"), bqs.name)
            for bq in bqs.bouquets:
                self.append_bouquet(bq, root)
            root_node.appendRow(root)

    def append_bouquet(self, bq, parent):
        name, bq_type, locked, hidden = bq.name, bq.type, bq.locked, bq.hidden
        row = (QStandardItem(bq.name), QStandardItem(locked), QStandardItem(hidden), QStandardItem(bq_type))
        parent.appendRow(row)
        bq_id = "{}:{}".format(name, bq_type)
        services = []
        extra_services = {}  # for services with different names in bouquet and main list
        agr = [None] * 7
        for srv in bq.services:
            fav_id = srv.data
            # IPTV and MARKER services
            s_type = srv.type
            if s_type in (BqServiceType.MARKER, BqServiceType.IPTV, BqServiceType.SPACE):
                icon = None
                picon_id = None
                data_id = srv.num
                locked = None

                if s_type is BqServiceType.IPTV:
                    icon = IPTV_ICON
                    fav_id_data = fav_id.lstrip().split(":")
                    if len(fav_id_data) > 10:
                        data_id = ":".join(fav_id_data[:11])
                        picon_id = "{}_{}_{}_{}_{}_{}_{}_{}_{}_{}.png".format(*fav_id_data[:10])
                        locked = LOCKED_ICON if data_id in self._blacklist else None
                srv = Service(None, None, icon, srv.name, locked, None, None, s_type.name,
                              self._picons.get(picon_id, None), picon_id, *agr, data_id, fav_id, None)
                self._services[fav_id] = srv
            elif s_type is BqServiceType.ALT:
                self._alt_file.add("{}:{}".format(srv.data, bq_type))
                srv = Service(None, None, None, srv.name, locked, None, None, s_type.name,
                              None, None, *agr, srv.data, fav_id, srv.num)
                self._services[fav_id] = srv
            elif srv.name:
                extra_services[fav_id] = srv.name
            services.append(fav_id)

        self._bouquets[bq_id] = services
        self._bq_file[bq_id] = bq.file
        if extra_services:
            self._extra_bouquets[bq_id] = extra_services

    def update_bouquet_services(self, bq_selected):
        """ Updates FAV model. """
        services = self._bouquets.get(bq_selected, [])
        ex_services = self._extra_bouquets.get(bq_selected, None)

        model = self.fav_view.model()
        model.clear()

        for srv_id in services:
            srv = self._services.get(srv_id, None)
            ex_srv_name = None
            if ex_services:
                ex_srv_name = ex_services.get(srv_id)
            if srv:
                # Setting background
                background = "color" if ex_srv_name else None
                srv_type = srv.service_type
                picon = self._picons.get(srv.picon_id, None)
                # Alternatives
                if srv.service_type == BqServiceType.ALT.name:
                    alt_servs = srv.transponder
                    if alt_servs:
                        alt_srv = self._services.get(alt_servs[0].data, None)
                        if alt_srv:
                            picon = self._picons.get(alt_srv.picon_id, None) if srv else None

                s_name = ex_srv_name if ex_srv_name else srv.service
                row_data = (srv.coded, s_name, picon, srv.locked, srv.hide, srv_type, srv.pos, srv.fav_id)
                model.appendRow((QStandardItem(i) for i in row_data))
        self.set_fav_headers()

    def clean_data(self):
        self.bouquets_view.model().clear()
        self.services_view.model().clear()
        self.fav_view.model().clear()

        for c in (self._bouquets, self._bq_file, self._extra_bouquets,
                  self._services, self._blacklist, self._alt_file, self._picons):
            c.clear()

    def set_services_headers(self):
        """ Sets services view headers. """
        # Setting visible columns.
        for c in (Column.SRV_CAS_FLAGS, Column.SRV_STANDARD, Column.SRV_CODED, Column.SRV_LOCKED, Column.SRV_HIDE,
                  Column.SRV_PICON_ID, Column.SRV_DATA_ID, Column.SRV_FAV_ID, Column.SRV_DATA_ID,
                  Column.SRV_TRANSPONDER):
            self.services_view.setColumnHidden(c, True)

        srv_view_labels = ("", "", "", "Service", "", "", "Package", "Type", "Picon",
                           "", "SID", "Frec", "SR", "Pol", "FEC", "System", "Pos")
        self.services_view.model().setHorizontalHeaderLabels(srv_view_labels)

    def set_fav_headers(self):
        """ Sets FAV view headers. """
        for c in (Column.FAV_CODED, Column.FAV_LOCKED, Column.FAV_HIDE, Column.FAV_ID):
            self.fav_view.setColumnHidden(c, True)
        fav_labels = ("", "Service", "Picon", "", "", "Type", "Pos")
        self.fav_view.model().setHorizontalHeaderLabels(fav_labels)

    # ******************** Satellites ******************** #

    def load_satellites(self, path):
        model = self.satellite_view.model()
        model.clear()

        root_node = model.invisibleRootItem()
        for sat in get_satellites(path):
            parent = QStandardItem(sat.name)
            for t in sat.transponders:
                parent.appendRow((QStandardItem(""),) + tuple(QStandardItem(i) for i in t))
            root_node.appendRow(parent)

        model.setHorizontalHeaderLabels(("Satellite", "Frec", "SR", "Pol", "FEC", "System", "Mod"))
        self.satellite_count_label.setText(str(model.rowCount()))

    # ******************** Streams ********************* #

    def playback_start(self, event=None):
        if self.current_page is not Page.STREAMS:
            return

        if not self._player:
            from app.streams.media import Player
            try:
                self._player = Player.make(self.settings.stream_lib, self.media_widget)
            except ImportError as e:
                self.log_text_browser.append(str(e))
                return

        indexes = self.fav_view.selectionModel().selectedIndexes()
        if not indexes or indexes[Column.FAV_TYPE].data() in self._marker_types or not self._http_api:
            return

        ref = self.get_service_ref(indexes[Column.FAV_ID].data(), indexes[Column.FAV_TYPE].data())
        self._http_api.send(HttpAPI.Request.STREAM, ref)

    def update_playback(self, data):
        """ Updates current URL for playback. """
        m3u = data.get("m3u", None)
        if m3u:
            self._player.play([s for s in str(m3u, "utf-8").split("\n") if not s.startswith("#")][0])

    def playback_stop(self):
        if self._player:
            self._player.stop()

    def show_full_screen(self, event=None):
        self.media_widget.hide()
        if self.media_widget.isFullScreen():
            self.media_widget.setWindowState(Qt.WindowNoState)
            self.media_widget.setWindowFlags(Qt.Widget)
        else:
            self.media_widget.setWindowFlags(Qt.Window)
            self.media_widget.setWindowState(Qt.WindowFullScreen)
        self.media_widget.show()

    # ********************** EPG *********************** #

    def update_single_epg(self, epg):
        event_list = epg.get("event_list", [])

        model = self.epg_view.model()
        model.clear()
        model.setColumnCount(3)

        for event in event_list:
            title = event.get("e2eventtitle", "")
            desc = event.get("e2eventdescription", "")
            start = int(event.get("e2eventstart", "0"))
            start_time = datetime.fromtimestamp(start)
            end_time = datetime.fromtimestamp(start + int(event.get("e2eventduration", "0")))
            time_header = "{} - {}".format(start_time.strftime("%A, %H:%M"), end_time.strftime("%H:%M"))
            model.appendRow(QStandardItem(i) for i in (title, time_header, desc))

        model.setHorizontalHeaderLabels(("Title", "Time", "Description"))

    def update_multiple_epg(self, epg):
        pass

    def get_service_ref(self, fav_id, srv_type):
        srv = self._services.get(fav_id, None)
        if srv:
            if srv_type == BqServiceType.IPTV.name:
                return srv.fav_id.strip()
            elif srv.picon_id:
                return srv.picon_id.rstrip(".png").replace("_", ":")

    # ********************* Timer ********************** #
    def on_timer_page_show(self):
        self._http_api.send(HttpAPI.Request.TIMER_LIST)

    def update_timer_list(self, timer_list):
        timer_list = timer_list.get("timer_list", [])
        model = self.timer_view.model()
        model.clear()

        for timer in timer_list:
            name = timer.get("e2name", "") or ""
            description = timer.get("e2description", "") or ""
            service_name = timer.get("e2servicename", "") or ""

            start_time = datetime.fromtimestamp(int(timer.get("e2timebegin", "0")))
            end_time = datetime.fromtimestamp(int(timer.get("e2timeend", "0")))
            time_str = "{} - {}".format(start_time.strftime("%A, %H:%M"), end_time.strftime("%H:%M"))

            model.appendRow(QStandardItem(i) for i in (name, description, service_name, time_str))
            model.setHorizontalHeaderLabels(("Name", "Description", "Service", "Time"))

    # ******************** HTTP API ******************** #

    @pyqtSlot()
    def update_state(self):
        self._http_api.send(self._http_api.Request.INFO)

    def update_state_info(self, info):
        info_text = "Connection status: {}. {}"
        if info and not info.get("error", None):
            image = info.get("e2distroversion", "")
            model = info.get("e2model", "")
            self.status_bar.showMessage(info_text.format("OK", "Current Box: {} Image: {}".format(model, image)))
        else:
            self.status_bar.showMessage(info_text.format("Disconnected.", ""))
            if self.log_action.isChecked():
                reason = info.get("reason", None)
                self.log_text_browser.append(reason) if reason else None

    def on_app_exit(self, state):
        self.close()

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


if __name__ == "__main__":
    pass
