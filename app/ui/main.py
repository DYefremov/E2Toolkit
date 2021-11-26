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
from collections import OrderedDict, Counter, defaultdict
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QTranslator, QStringListModel, QTimer, pyqtSlot, Qt, QFile, QDir
from PyQt5.QtGui import QIcon, QStandardItem, QPixmap
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog, QActionGroup, QAction, QInputDialog

from app.commons import APP_VERSION, APP_NAME, LANG_PATH, log, LOCALES
from app.connections import HttpAPI, DownloadType, DataLoader, PiconDeleter
from app.enigma.backup import backup_data, clear_data_path
from app.enigma.blacklist import write_blacklist
from app.enigma.bouquets import BouquetsReader, BouquetsWriter
from app.enigma.ecommons import BqServiceType, Service, Bouquet, Bouquets, BqType, BouquetService
from app.enigma.lamedb import LameDbWriter, LameDbReader
from app.satellites.satxml import get_satellites, write_satellites
from app.streams.iptv import import_m3u
from app.ui.dialogs import *
from app.ui.settings import SettingsDialog, Settings
from app.ui.uicommons import Column, IPTV_ICON, LOCKED_ICON, BqGenType
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
        self._bq_selected = ""
        self._bouquets = {}
        self._bq_file = {}
        self._extra_bouquets = {}
        self._services = {}
        self._blacklist = set()
        self._alt_file = set()
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
        self.init_last_config()

    def init_ui(self):
        self.resize(self.settings.app_window_size)

    def init_actions(self):
        # File menu.
        self.import_action.triggered.connect(self.on_data_import)
        self.open_action.triggered.connect(self.on_data_open)
        self.extract_action.triggered.connect(self.on_data_extract)
        self.save_action.triggered.connect(self.on_data_save)
        self.save_as_action.triggered.connect(self.on_data_save_as)
        self.exit_action.triggered.connect(self.on_app_exit)
        # Backup
        self.backup_restore_action.triggered.connect(self.on_data_restore)
        # Settings.
        self.settings_action.triggered.connect(self.on_settings_dialog)
        # Toolbar.
        self.download_tool_button.clicked.connect(self.on_data_download)
        self.upload_tool_button.clicked.connect(self.on_data_upload)
        # Bouquets.
        self.bouquets_view.selectionModel().selectionChanged.connect(self.on_bouquet_selection)
        self.fav_view.selectionModel().selectionChanged.connect(self.on_fav_selection)
        self.fav_view.edited.connect(lambda r: self.on_service_edit(r, self.fav_view.model()))
        self.fav_view.removed.connect(self.remove_favorites)
        self.fav_view.inserted.connect(self.on_fav_data_changed)
        self.fav_view.picon_assigned.connect(lambda d: self.copy_picons(*d))
        self.services_view.edited.connect(lambda r: self.on_service_edit(r, self.services_view.model()))
        self.services_view.removed.connect(self.remove_services)
        self.services_view.delete_release.connect(self.on_service_remove_done)
        self.services_view.context_menu.copy_to_top_action.triggered.connect(self.on_to_fav_top_copy)
        self.services_view.context_menu.copy_to_end_action.triggered.connect(self.on_to_fav_end_copy)
        self.services_view.gen_bouquets.connect(self.gen_bouquets)
        self.services_view.picon_assigned.connect(lambda d: self.copy_picons(*d))
        self.bouquets_view.removed.connect(self.remove_bouquets)
        self.bouquets_view.context_menu.new_action.triggered.connect(self.on_new_bouquet_add)
        self.add_bouquet_button.clicked.connect(self.on_new_bouquet_add)
        # Satellites.
        self.satellite_view.selectionModel().currentRowChanged.connect(self.on_satellite_selection)
        self.satellite_view.add.connect(self.on_satellite_add)
        self.satellite_view.edited.connect(self.on_satellite_edit)
        self.transponder_view.add.connect(self.on_transponder_add)
        self.transponder_view.edited.connect(self.on_transponder_edit)
        self.transponder_view.removed.connect(self.on_transponder_remove)
        # Picons.
        self.picon_src_view.id_received.connect(self.on_picon_ids_received)
        self.picon_src_view.urls_received.connect(self.on_picon_urls_received)
        self.picon_src_view.replaced.connect(self.on_picon_replace)
        self.picon_dst_view.id_received.connect(self.on_picon_ids_received)
        self.picon_dst_view.urls_received.connect(self.on_picon_urls_received)
        self.picon_dst_view.replaced.connect(self.on_picon_replace)
        self.picon_dst_view.removed.connect(self.on_picon_remove)
        self.picon_dst_view.remove_from_receiver.connect(self.on_picon_remove_from_receiver)
        # Streams.
        self.media_play_tool_button.clicked.connect(self.playback_start)
        self.media_stop_tool_button.clicked.connect(self.playback_stop)
        self.media_full_tool_button.clicked.connect(self.show_full_screen)
        self.fav_view.double_clicked.connect(self.playback_start)
        self.media_widget.double_clicked.connect(self.show_full_screen)
        # IPTV
        self.import_m3u_action.triggered.connect(self.on_import_m3u)
        self.add_stream_action.triggered.connect(self.on_add_iptv_service)
        # Timers.
        self.timer_add_button.clicked.connect(self.on_timer_add)
        self.timer_remove_button.clicked.connect(self.on_timer_remove)
        self.timer_view.edited.connect(self.on_timer_edit)
        self.timer_view.removed.connect(self.on_timer_remove)
        self.epg_view.timer_add.connect(self.on_timer_add_from_event)
        # Remote controller actions.
        self.control_up_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.UP))
        self.control_down_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.DOWN))
        self.control_left_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.LEFT))
        self.control_right_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.RIGHT))
        self.control_ok_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.OK))
        self.control_menu_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.MENU))
        self.control_exit_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.EXIT))
        self.control_info_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.INFO))
        self.control_back_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.BACK))
        self.red_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.RED))
        self.green_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.GREEN))
        self.yellow_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.YELLOW))
        self.blue_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.BLUE))
        # Media
        self.media_prev_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.PLAYER_PREV))
        self.media_next_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.PLAYER_NEXT))
        self.media_play_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.PLAYER_PLAY))
        self.media_stop_button.clicked.connect(lambda b: self.on_remote_action(HttpAPI.Remote.PLAYER_STOP))
        # Power
        self.power_standby_button.clicked.connect(lambda b: self.on_power_action(HttpAPI.Power.STANDBY))
        self.power_wake_up_button.clicked.connect(lambda b: self.on_power_action(HttpAPI.Power.WAKEUP))
        self.power_reboot_button.clicked.connect(lambda b: self.on_power_action(HttpAPI.Power.REBOOT))
        self.power_restart_gui_button.clicked.connect(lambda b: self.on_power_action(HttpAPI.Power.RESTART_GUI))
        self.power_shutdown_button.clicked.connect(lambda b: self.on_power_action(HttpAPI.Power.DEEP_STANDBY))
        # Screenshots
        self.screenshot_all_button.clicked.connect(self.on_screenshot_all)
        self.screenshot_video_button.clicked.connect(self.on_screenshot_video)
        self.screenshot_osd_button.clicked.connect(self.on_screenshot_osd)
        # Volume
        self.control_volume_dial.valueChanged.connect(self.on_volume_changed)
        # HTTP API.
        self._update_state_timer.timeout.connect(self.update_state)
        # About.
        self.about_action.triggered.connect(self.on_about)
        # Context menu items.
        self.services_view.copied.connect(self.fav_view.context_menu.paste_action.setEnabled)
        # Search.
        self.service_search_edit.textChanged.connect(self.services_view.search)
        self.bq_service_search_edit.textChanged.connect(self.fav_view.search)
        self.epg_search_edit.textChanged.connect(self.epg_view.search)
        self.timer_search_edit.textChanged.connect(self.timer_view.search)

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
        picon_path = self.get_picon_path()
        self.services_view.model().picon_path = picon_path
        self.fav_view.model().picon_path = picon_path

    def init_http_api(self):
        if self._http_api:
            self._update_state_timer.stop()

        callbacks = {HttpAPI.Request.INFO: self.update_state_info,
                     HttpAPI.Request.SIGNAL: self.update_signal,
                     HttpAPI.Request.STREAM: self.update_playback,
                     HttpAPI.Request.TIMER_LIST: self.update_timer_list,
                     HttpAPI.Request.EPG: self.update_single_epg,
                     HttpAPI.Request.GRUB: self.update_screenshot,
                     HttpAPI.Request.REMOTE: self.on_action_done,
                     HttpAPI.Request.VOL: self.on_action_done}

        self._http_api = HttpAPI(self._profiles.get(self.profile_combo_box.currentText()), callbacks)
        self._update_state_timer.start(3000)

    def init_last_config(self):
        """ Initialization of the last configuration. """
        if self.settings.load_last_config:
            config = self.settings.last_config
            self.profile_combo_box.setCurrentText(config.get("last_profile", ""))
            self.load_data()
            last_bouquet = config.get("last_bouquet", (-1, -1, -1, -1))
            # Last selected bouquet.
            sel_model = self.bouquets_view.selectionModel()
            root_index = self.bouquets_view.model().index(last_bouquet[0], last_bouquet[1])
            index = root_index.child(last_bouquet[2], last_bouquet[3])
            sel_model.select(index, sel_model.ClearAndSelect | sel_model.Rows)
            sel_model.setCurrentIndex(index, sel_model.NoUpdate)

    def on_settings_dialog(self, state):
        SettingsDialog()
        self.init_profiles()

    def set_locale(self, locale):
        app = Application.instance()
        app.set_locale(locale)
        self.retranslate_ui(self)

    def closeEvent(self, event):
        """ Main window close event. """
        self.settings.app_window_size = self.size()
        if self.settings.load_last_config:
            config = {"last_profile": self.profile_combo_box.currentText()}
            indexes = self.bouquets_view.selectionModel().selectedIndexes()
            if indexes:
                index = indexes[0]
                parent = index.parent()
                config["last_bouquet"] = (parent.row(), parent.column(), index.row(), index.column())
            else:
                config["last_bouquet"] = (-1, -1, -1, -1)
            self.settings.last_config = config

    # ******************** Data loading. ******************** #

    def on_data_download(self, state=False):
        self.download_tool_button.setEnabled(False)
        self.upload_tool_button.setEnabled(False)
        self.log_text_browser.clear()

        data_loader = self.get_data_loader()
        data_loader.start()

    def on_data_load_done(self, download_type):
        self.download_tool_button.setEnabled(True)
        self.upload_tool_button.setEnabled(True)
        if download_type is DownloadType.SATELLITES:
            self.load_satellites(self.get_data_path() + "satellites.xml")
        if download_type is DownloadType.PICONS:
            self.load_picons()
        else:
            self.load_data()

    def on_data_upload(self):
        if QMessageBox.question(self, APP_NAME, self.tr("Are you sure?")) != QMessageBox.Yes:
            return

        self.upload_tool_button.setEnabled(False)
        self.download_tool_button.setEnabled(False)
        self.log_text_browser.clear()

        data_loader = self.get_data_loader(upload=True)
        data_loader.start()

    def on_data_upload_done(self, download_type):
        self.upload_tool_button.setEnabled(True)
        self.download_tool_button.setEnabled(True)

    def get_data_loader(self, upload=False):
        """ Creates and returns DataLoader class instance. """
        download_type = DownloadType.ALL
        f_filter = None
        if self.current_page is Page.SAT:
            download_type = DownloadType.SATELLITES
        elif self.current_page is Page.PICONS:
            download_type = DownloadType.PICONS
            if self.picon_load_only_selected_box.isChecked():
                f_filter = self.selected_dst_picons()

        data_loader = DataLoader(self.settings, download_type, upload, self._http_api, f_filter, parent=self)
        data_loader.message.connect(self.log_text_browser.append)
        data_loader.http.connect(self.http_send_callback)
        data_loader.error_message.connect(self.on_data_load_error)
        data_loader.loaded.connect(self.on_data_upload_done if upload else self.on_data_load_done)

        return data_loader

    def on_data_load_error(self, msg):
        self.status_bar.showMessage(msg)
        self.log_text_browser.setVisible(True)
        self.upload_tool_button.setEnabled(True)
        self.download_tool_button.setEnabled(True)

    def http_send_callback(self, commands):
        self._http_api.send(commands[0])
        self.log_text_browser.append(commands[1])

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
                self.load_picons(resp + os.sep)
        else:
            QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_data_extract(self, state):
        resp = QFileDialog.getOpenFileName(self, self.tr("Select Archive"), str(Path.home()),
                                           "Archive files (*.gz *.zip)", )
        if all(resp):
            self.load_compressed_data(resp[0])

    def on_data_restore(self, state):
        backup_dialog = BackupDialog(self.get_backup_path(), self.get_data_path())
        backup_dialog.extracted.connect(self.load_data)
        backup_dialog.exec()

    def get_data_path(self):
        profile = self._profiles.get(self.profile_combo_box.currentText())
        return "{}{}{}".format(self.settings.data_path, profile["name"], os.sep)

    def get_picon_path(self):
        return "{}{}{}".format(self.settings.picon_path, self.profile_combo_box.currentText(), os.sep)

    def get_backup_path(self):
        return "{}{}{}".format(self.settings.backup_path, self.profile_combo_box.currentText(), os.sep)

    def load_data(self, path=None):
        if not path:
            path = self.get_data_path()

        try:
            self.clean_data()
            bouquets = BouquetsReader(path).get()
            services = LameDbReader(path).parse()
        except FileNotFoundError as e:
            msg = self.tr("Please, download files from receiver or setup your path for read data!")
            self.show_error_dialog(msg)
            log(e)
        else:
            self.append_data(bouquets, services)

    def load_compressed_data(self, data_path):
        """ Opening archived data.  """
        arch_path = self.get_archive_path(data_path)
        if arch_path:
            if self.current_page is Page.BOUQUETS:
                self.load_data(arch_path.name + os.sep)
            elif self.current_page is Page.SAT:
                s_path = arch_path.name + os.sep + "satellites.xml"
                if os.path.exists(s_path):
                    self.load_satellites(s_path)
                else:
                    self.show_error_dialog(self.tr("File not found!"))

            arch_path.cleanup()

    def get_archive_path(self, data_path):
        """ Returns the temp dir path for the extracted data, or None if the archive format is not supported. """
        import zipfile
        import tarfile
        import tempfile

        tmp_path = tempfile.TemporaryDirectory()
        tmp_path_name = tmp_path.name

        if zipfile.is_zipfile(data_path):
            with zipfile.ZipFile(data_path) as zip_file:
                for zip_info in zip_file.infolist():
                    if not zip_info.filename.endswith(os.sep):
                        zip_info.filename = os.path.basename(zip_info.filename)
                        zip_file.extract(zip_info, path=tmp_path_name)
        elif tarfile.is_tarfile(data_path):
            with tarfile.open(data_path) as tar:
                for mb in tar.getmembers():
                    if mb.isfile():
                        mb.name = os.path.basename(mb.name)
                        tar.extract(mb, path=tmp_path_name)
        else:
            tmp_path.cleanup()
            log("Error getting the path for the archive. Unsupported file format: {}".format(data_path))
            self.show_error_dialog(self.tr("Unsupported format!"))
            return

        return tmp_path

    def append_data(self, bouquets, services):
        self.append_bouquets(bouquets)
        self.append_services(services)

    def append_services(self, services):
        model = self.services_view.model()
        for s in services:
            self._services[s.fav_id] = s
            model.appendRow(QStandardItem(i) for i in s)

        self.update_services_count(services)

    def append_bouquets(self, bouquets):
        model = self.bouquets_view.model()
        root_node = model.invisibleRootItem()
        for i, bqs in enumerate(bouquets):
            root = QStandardItem(QIcon.fromTheme("tv-symbolic" if i == 0 else "radio-symbolic"), bqs.name)
            root.setDragEnabled(False)
            for bq in bqs.bouquets:
                self.append_bouquet(bq, root)
            root_node.appendRow(root)

    def append_bouquet(self, bq, parent):
        name, bq_type, locked, hidden = bq.name, bq.type, bq.locked, bq.hidden
        row = (QStandardItem(bq.name), QStandardItem(locked), QStandardItem(hidden), QStandardItem(bq_type))
        parent.appendRow(row)
        bq_id = f"{name}:{bq_type}"
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
                data_id = str(srv.num)
                locked = None

                if s_type is BqServiceType.IPTV:
                    icon = IPTV_ICON
                    fav_id_data = fav_id.lstrip().split(":")
                    if len(fav_id_data) > 10:
                        data_id = ":".join(fav_id_data[:11])
                        picon_id = "{}_{}_{}_{}_{}_{}_{}_{}_{}_{}.png".format(*fav_id_data[:10])
                        locked = LOCKED_ICON if data_id in self._blacklist else None
                srv = Service(None, None, icon, None, picon_id, srv.name, locked, None,
                              None, s_type.name, *agr, data_id, fav_id, None)
                self._services[fav_id] = srv
            elif s_type is BqServiceType.ALT:
                self._alt_file.add(f"{srv.data}:{bq_type}")
                srv = Service(None, None, None, None, None, srv.name, locked, None, None, s_type.name,
                              *agr, srv.data, fav_id, srv.num)
                self._services[fav_id] = srv
            elif s_type is BqServiceType.BOUQUET:
                # Sub bouquets!
                msg = "Detected sub-bouquets! This feature is not fully supported yet!"
                QMessageBox.information(self, APP_NAME, self.tr(msg))
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

        self.fav_view.clear_data()
        model = self.fav_view.model()

        for srv_id in services:
            srv = self._services.get(srv_id, None)
            ex_srv_name = None
            if ex_services:
                ex_srv_name = ex_services.get(srv_id)
            if srv:
                # Alternatives
                if srv.service_type == BqServiceType.ALT.name:
                    alt_servs = srv.transponder
                    if alt_servs:
                        alt_srv = self._services.get(alt_servs[0].data, None)
                        srv = srv._replace(transponder=None)

                srv = srv._replace(name=ex_srv_name) if ex_srv_name else srv
                model.appendRow((QStandardItem(i) for i in srv))

    def clean_data(self):
        self.bouquets_view.clear_data()
        self.services_view.clear_data()
        self.fav_view.clear_data()
        self.service_filter_edit.setText("")

        for c in (self._bouquets, self._bq_file, self._extra_bouquets, self._services, self._blacklist, self._alt_file):
            c.clear()

    # ********************* Data save. ********************* #

    def on_data_save(self):
        if QMessageBox.question(self, APP_NAME, self.tr("Are you sure?")) != QMessageBox.Yes:
            return

        if self.current_page is Page.BOUQUETS:
            if self.bouquets_view.model().rowCount():
                self.save_data(self.get_data_path())
            else:
                self.show_error_dialog(self.tr("No data to save!"))
        elif self.current_page is Page.SAT:
            self.save_satellites()
        else:
            QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_data_save_as(self):
        resp = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"), str(Path.home()))
        if not resp:
            return

        if os.listdir(resp):
            msg = "{}\n\t{}".format(self.tr("The selected folder already contains files!"), self.tr("Are you sure?"))
            if QMessageBox.question(self, APP_NAME, msg) != QMessageBox.Yes:
                return
        self.save_data(resp + os.sep, False)

    def save_data(self, path, force_backup=True):
        if self.settings.backup_before_save and force_backup:
            backup_data(path, self.get_backup_path())
        else:
            clear_data_path(path)
        # Processing bouquets.
        model = self.bouquets_view.model()
        bq_tv_index, bq_radio_index = model.index(0, Column.BQ_NAME), model.index(1, Column.BQ_NAME)
        bouquets = []
        #  TV bouquets processing.
        tv_bqs = [self.get_bouquet(model.index(i, Column.BQ_NAME, bq_tv_index).data(),
                                   model.index(i, Column.BQ_LOCKED, bq_tv_index).data(),
                                   model.index(i, Column.BQ_HIDDEN, bq_tv_index).data(),
                                   model.index(i, Column.BQ_TYPE, bq_tv_index).data()) for i in
                  range(model.rowCount(bq_tv_index))]
        bouquets.append(Bouquets(bq_tv_index.data(), BqType.TV.value, tv_bqs))
        # Radio bouquets processing.
        radio_bqs = [self.get_bouquet(model.index(i, Column.BQ_NAME, bq_radio_index).data(),
                                      model.index(i, Column.BQ_LOCKED, bq_radio_index).data(),
                                      model.index(i, Column.BQ_HIDDEN, bq_radio_index).data(),
                                      model.index(i, Column.BQ_TYPE, bq_radio_index).data()) for i in
                     range(model.rowCount(bq_radio_index))]
        bouquets.append(Bouquets(bq_radio_index.data(), BqType.RADIO.value, radio_bqs))
        # Bouquets writing.
        BouquetsWriter(path, bouquets).write()

        # Processing services.
        model = self.services_view.model()
        c_count = model.columnCount()
        services = (Service(*(model.index(r, c).data() for c in range(c_count))) for r in range(model.rowCount()))
        LameDbWriter(path, services).write()
        # Blacklist.
        write_blacklist(path, self._blacklist)

        QMessageBox.information(self, APP_NAME, self.tr("Done!"))

    def save_satellites(self):
        r_count = self.satellite_view.model().rowCount()
        if not r_count:
            self.show_error_dialog(self.tr("No data to save!"))
            return

        model = self.satellite_view.model()
        write_satellites((model.index(r, Column.SAT_DATA).data(Qt.UserRole) for r in range(r_count)),
                         self.get_data_path() + "satellites.xml")

    # ******************* Data import ******************** #

    def on_import_m3u(self):
        """ Imports iptv from m3u files. """
        if not self._bq_selected:
            self.show_error_dialog(self.tr("No bouquet is selected!"))
            return

        resp = QFileDialog.getOpenFileName(self, self.tr("Select *.m3u file"), str(Path.home()),
                                           "Playlist files (*.m3u *.m3u8)", )
        if all(resp):
            services = import_m3u(resp[0])
            self.append_imported_services(services)

    def append_imported_services(self, services):
        self.fav_view.scrollToBottom()
        bq_services = self._bouquets.get(self._bq_selected)
        for srv in services:
            self._services[srv.fav_id] = srv
            bq_services.append(srv.fav_id)
        self.update_bouquet_services(self._bq_selected)

    def on_add_iptv_service(self):
        if not self._bq_selected:
            self.show_error_dialog(self.tr("No bouquet is selected!"))
            return

        service_dialog = IptvServiceDialog()
        if service_dialog.exec():
            row = self.fav_view.currentIndex().row()
            service = service_dialog.service
            model = self.fav_view.model()
            bq = self._bouquets.get(self._bq_selected, None)
            if row < 0:
                model.appendRow(QStandardItem(i) for i in service)
                self.fav_view.scrollToBottom()
                self.fav_view.selectRow(model.rowCount() - 1)
                bq.append(service.fav_id)
            else:
                model.insertRow(row + 1, (QStandardItem(i) for i in service))
                bq.insert(row + 1, service.fav_id)
            self._services[service.fav_id] = service

    # ********************* Bouquets ********************* #

    def on_new_bouquet_add(self):
        model = self.bouquets_view.model()
        if not model.rowCount():
            self.show_error_dialog(self.tr("No data loaded!"))
            return

        name, resp = QInputDialog.getText(self, "E2Toolkit [New bouquet]", self.tr("Enter the name of the bouquet."))
        if not resp:
            return
        # Checking if the given name is already present.
        if self._bouquets.keys() & {"{}:{}".format(name, BqType.TV.value), "{}:{}".format(name, BqType.RADIO.value)}:
            self.show_error_dialog(self.tr("A bouquet with that name exists!"))
            return

        cur_index = self.bouquets_view.currentIndex()
        parent_row = cur_index.parent().row()
        root_item = model.item(cur_index.row() if parent_row < 0 else cur_index.parent().row(), 0)
        if not root_item:
            log("Error creation of root item [on_new_bouquet_add].")
            return

        b_type = BqType.RADIO.value if root_item.row() > 0 else BqType.TV.value
        bq = (QStandardItem(name), None, None, QStandardItem(b_type))
        row = 0 if parent_row < 0 else cur_index.row() + 1
        root_item.insertRow(row, bq)
        self._bouquets["{}:{}".format(name, b_type)] = []

    def on_bouquet_selection(self, selected_item, deselected_item):
        indexes = selected_item.indexes()
        if len(indexes) > 1:
            self._bq_selected = "{}:{}".format(indexes[Column.BQ_NAME].data(), indexes[Column.BQ_TYPE].data())
            self.update_bouquet_services(self._bq_selected)

    def on_fav_selection(self, selected_item, deselected_item):
        if self.current_page is Page.EPG and self._http_api:
            ind = selected_item.indexes()

            if len(ind) == self.fav_view.model().columnCount():
                ref = self.get_service_ref(ind[Column.FAV_ID].data(), ind[Column.TYPE].data())
                self._http_api.send(self._http_api.Request.EPG, ref)
                self.fav_view.setEnabled(False)

    def on_fav_data_changed(self):
        """  Refreshes the current bouquet services list.

            Called when the data in the favorites model has changed [insert, move, etc.].
        """
        bq = self._bouquets.get(self._bq_selected, None)
        if bq is None:
            return

        bq.clear()
        model = self.fav_view.model()
        for r in range(model.rowCount()):
            bq.append(model.index(r, Column.FAV_ID).data())

    def on_service_edit(self, row, model):
        service = self._services.get(model.index(row, Column.FAV_ID).data(), None)
        if service:
            s_type = service.service_type
            if s_type in self._marker_types:
                return

            dialog = IptvServiceDialog(service) if s_type == BqServiceType.IPTV.value else ServiceDialog(service)
            if dialog.exec():
                self._services.pop(service.fav_id, None)
                service = dialog.service
                self._services[service.fav_id] = service
                [model.setData(model.index(row, c), d) for c, d in enumerate(service)]

    def remove_services(self, rows):
        list(map(lambda s: self._services.pop(s, None), rows.values()))
        # Fav model update.
        ids = set(rows.values())
        model = self.fav_view.model()
        sel_model = self.fav_view.selectionModel()
        for k, v in {model.index(r, 0): model.index(r, Column.FAV_ID).data() for r in range(model.rowCount())}.items():
            if v in ids:
                # Rows selection to delete.
                sel_model.select(k, sel_model.Select | sel_model.Rows)
        self.fav_view.on_remove()

    def on_service_remove_done(self):
        self.update_services_count(filter(lambda s: s.pos, self._services.values()))

    def remove_favorites(self, rows):
        bq = self._bouquets.get(self._bq_selected, None)
        if bq:
            list(map(bq.pop, rows))

    def remove_bouquets(self, rows):
        bqs = {"{}:{}".format(r[Column.BQ_NAME].data(), r[Column.BQ_TYPE].data()) for r in rows}
        list(map(self._bouquets.pop, bqs))
        self.fav_view.clear_data() if self._bq_selected in bqs else None

    def update_services_count(self, services):
        """ Updates service counters. """
        counter = Counter(s.service_type for s in services)
        self.data_count_label.setText(str(counter.get("Data", 0)))
        self.radio_count_label.setText(str(counter.get("Radio", 0)))
        self.tv_count_label.setText(str(sum(v for k, v in counter.items() if k not in {"Data", "Radio"})))

    def get_bouquet(self, bq_name, locked, hidden, bq_type):
        """ Constructs and returns Bouquet class instance. """
        bq_id = "{}:{}".format(bq_name, bq_type)
        ext_services = self._extra_bouquets.get(bq_id, None)
        bq_s = list(filter(None, [self._services.get(f_id, None) for f_id in self._bouquets.get(bq_id, [])]))
        bq_s = self.get_bq_services(bq_s, ext_services)

        return Bouquet(bq_name, bq_type, bq_s, locked, hidden, self._bq_file.get(bq_id, None))

    def get_bq_services(self, services, ext_services):
        """ Preparing a list of services for the Enigma2 bouquet. """
        s_list = []
        for srv in services:
            if srv.service_type == BqServiceType.ALT.name:
                # Alternatives to service in a bouquet.
                alts = list(map(lambda s: s._replace(name=None),
                                filter(None, [self._services.get(s.data, None) for s in srv.transponder or []])))
                s_list.append(srv._replace(transponder=alts))
            else:
                # Extra names for service in bouquet.
                s_list.append(srv._replace(name=ext_services.get(srv.fav_id, None) if ext_services else None))
        return s_list

    def on_to_fav_top_copy(self):
        self.fav_view.scrollToTop()
        self.copy_to(self.services_view, self.fav_view, self.fav_view.model().index(-1, 0))

    def on_to_fav_end_copy(self):
        self.fav_view.scrollToBottom()
        model = self.fav_view.model()
        self.copy_to(self.services_view, self.fav_view, model.index(model.rowCount() - 1, 0))

    def copy_to(self, src_view, dst_view, index):
        dst_view.setCurrentIndex(index)
        src_view.on_copy()
        dst_view.on_paste()

    def gen_bouquets(self, gen_type):
        """ Creates and adds bouquets of the given type. """
        column = Column.POS
        if gen_type in (BqGenType.PACKAGE, BqGenType.EACH_PACKAGE):
            column = Column.PACKAGE
        elif gen_type in (BqGenType.TYPE, BqGenType.EACH_TYPE):
            column = Column.TYPE

        rows = self.services_view.selectionModel().selectedRows(column)
        if not rows:
            return

        if len(rows) > 1:
            self.show_error_dialog(self.tr("Please, select only one item!"))
            return

        cond = rows[0].data()
        bouquets = []

        model = self.services_view.model()
        values = {model.index(i, column).data() for i in range(model.rowCount())}
        exist = {k.rstrip(":tv").rstrip(":radio") for k in self._bouquets.keys()} & values
        # Splitting services by column value.
        d = defaultdict(list)
        [d[model.index(r, column).data()].append(
            BouquetService(model.index(r, Column.NAME).data(),
                           BqServiceType.DEFAULT,
                           model.index(r, Column.FAV_ID).data(),
                           0)) for r in range(model.rowCount())]

        if gen_type in (BqGenType.SAT, BqGenType.PACKAGE, BqGenType.TYPE):
            bouquets.append(Bouquet(cond, BqType.TV.value, d.get(cond)))
        else:
            for name in filter(lambda v: v not in exist, values):
                bouquets.append(Bouquet(name, BqType.TV.value, d.get(name)))

        tv_root_item = self.bouquets_view.model().item(0, Column.BQ_NAME)
        for bq in bouquets:
            self.append_bouquet(bq, tv_root_item)

    # ******************** Satellites ******************** #

    def on_satellite_page_show(self):
        if not self.satellite_view.model().rowCount():
            self.load_satellites(self.get_data_path() + "satellites.xml")

    def load_satellites(self, path):
        try:
            satellites = get_satellites(path)
        except FileNotFoundError as e:
            log(e)
        else:
            self.satellite_view.clear_data()
            model = self.satellite_view.model()
            [model.appendRow((self.get_satellite_row(sat))) for sat in satellites]
            self.satellite_count_label.setText(str(model.rowCount()))

    def on_satellite_selection(self, selected, deselected):
        self.transponder_view.clear_data()

        t_model = self.transponder_view.model()
        sat = self.satellite_view.model().index(selected.row(), Column.SAT_DATA).data(Qt.UserRole)
        if sat:
            for t in sat.transponders:
                t_model.appendRow(QStandardItem(i) for i in t)

        self.satellite_transponder_count_label.setText(str(t_model.rowCount()))

    def on_satellite_add(self):
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_transponder_add(self):
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_satellite_edit(self, row):
        model = self.satellite_view.model()
        index = model.index(row, Column.SAT_DATA)
        sat_dialog = SatelliteDialog(index.data(Qt.UserRole))

        if sat_dialog.exec():
            satellite = sat_dialog.satellite
            model.setData(index, satellite, Qt.UserRole)
            model.setData(model.index(row, Column.SAT_NAME), satellite.name)
            model.setData(model.index(row, Column.SAT_POS), self.get_sat_position(int(satellite.position)))

    def get_satellite_row(self, satellite):
        """ Returns the satellite row representation as a QStandardItem tuple. """
        sat_item = QStandardItem("satellite")
        sat_item.setData(satellite, Qt.UserRole)

        return QStandardItem(satellite.name), QStandardItem(self.get_sat_position(int(satellite.position))), sat_item

    def get_sat_position(self, sat_pos):
        return f"{abs(sat_pos / 10):0.1f}{'W' if sat_pos < 0 else 'E'}"

    def on_transponder_edit(self, row):
        sat_model = self.satellite_view.model()
        sat_index = sat_model.index(self.satellite_view.currentIndex().row(), Column.SAT_DATA)
        sat = sat_index.data(Qt.UserRole)
        if not sat:
            return

        tr_dialog = TransponderDialog(sat.transponders[row])
        if tr_dialog.exec():
            transponder = tr_dialog.transponder
            sat.transponders[row] = transponder
            t_model = self.transponder_view.model()
            [t_model.setData(t_model.index(row, c), d) for c, d in enumerate(transponder)]
            sat_model.setData(sat_index, sat, Qt.UserRole)

    def on_transponder_remove(self, rows):
        rows = sorted(rows, reverse=True)
        if not rows:
            return

        model = self.satellite_view.model()
        data_index = model.index(self.satellite_view.currentIndex().row(), Column.SAT_DATA)
        sat = data_index.data(Qt.UserRole)
        if sat:
            list(map(sat.transponders.pop, rows))
            model.setData(data_index, sat, Qt.UserRole)
            self.satellite_transponder_count_label.setText(str(len(sat.transponders)))

    # ********************** Picons ********************** #

    def on_picon_page_show(self):
        self.picon_src_box.setVisible(False)
        self.load_picons()

    def on_picon_ids_received(self, ids):
        view = ids[0]
        index = view.indexAt(view.mapFromGlobal(view.cursor().pos()))
        if not index.isValid():
            return

        self.copy_picons(view.model().index(index.row(), Column.PICON_PATH).data(), ids[1])

    def copy_picons(self, src, ids):
        src_file = QFile(src)
        if not src_file.exists():
            return

        src = src_file.fileName()
        p_dir = QDir(self.get_picon_path())
        if not p_dir.exists(p_dir.path()):
            p_dir.mkpath(p_dir.path())

        for p_id in ids:
            file = QFile(p_dir.path() + p_dir.separator() + p_id)
            if file.exists():
                file.remove()

            file.copy(src, file.fileName())

    def on_picon_urls_received(self, urls):
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_picon_replace(self, picons):
        view = picons[0]
        if view is self.picon_src_view:
            self.show_error_dialog(self.tr("Not allowed in this context!"))
            return

        paths = picons[1]
        if len(paths) > 1:
            self.show_error_dialog(self.tr("Please, select only one item!"))
            return

        index = view.indexAt(view.mapFromGlobal(view.cursor().pos()))
        if not index.isValid():
            return

        dst = view.model().index(index.row(), Column.PICON_PATH).data()
        file = QFile(dst)
        if file.exists():
            file.remove()

        file.copy(paths[0], file.fileName())

    def load_picons(self, path=None):
        self.picon_dst_view.clear_data()
        ids = {s.picon_id: s.fav_id for s in self._services.values()}
        self.append_picons(Path(self.get_picon_path()), self.picon_dst_view.model(), ids)

        if path:
            self.picon_src_box.setVisible(True)
            self.append_picons(Path(path), self.picon_src_view.model(), ids)

    def append_picons(self, path, model, ids):
        """ Appends picons to the given model.

            @param path: load path.
            @param model: model to add data.
            @param ids: service ids.
        """
        for f in path.glob("*.png"):
            info = self.get_service_info(self._services.get(ids.get(f.name, None), None))
            model.appendRow((QStandardItem(info if info else f.name), QStandardItem(str(f)), None))

    def get_service_info(self, srv):
        """ Returns info string representation about the service. """
        if not srv:
            return ""

        header = "{}: {}\n{}: {}\n{}: {}\n".format(self.tr("Name"), srv.name,
                                                   self.tr("Type"), srv.service_type,
                                                   self.tr("Package"), srv.package)
        ref = "{}: {}".format(self.tr("Service reference"), srv.picon_id.rstrip(".png"))
        return "{}\n{}".format(header, ref)

    def selected_dst_picons(self):
        """ Returns a set of selected picon files from the dst view. """
        return {Path(r.data()).name for r in self.picon_dst_view.selectionModel().selectedRows(Column.PICON_PATH)}

    def on_picon_remove(self, rows):
        paths = (self.picon_dst_view.model().index(r, Column.PICON_PATH).data() for r in rows)
        list(map(lambda p: QFile(p).remove(), paths))

    def on_picon_remove_from_receiver(self, rows):
        paths = {Path(self.picon_dst_view.model().index(r, Column.PICON_PATH).data()).name for r in rows}
        deleter = PiconDeleter(self.settings, paths, parent=self)
        deleter.message.connect(self.log_text_browser.append)
        deleter.error_message.connect(self.on_data_load_error)
        deleter.loaded.connect(lambda: QMessageBox.information(self, APP_NAME, self.tr("Done!")))
        deleter.start()

    # ******************** Streams ********************* #

    def playback_start(self, event=None):
        self.streams_tool_button.toggle()

        if not self._player:
            from app.streams.media import Player
            try:
                self._player = Player.make(self.settings.stream_lib, self.media_widget)
                self._player.audio_track.connect(self.update_audio_tracks)
                self._player.subtitle_track.connect(self.update_subtitle_tracks)
                self._player.error.connect(self.show_error_dialog)
            except ImportError as e:
                self.show_error_dialog(str(e))
                self.log_text_browser.append(str(e))
                return

        indexes = self.fav_view.selectionModel().selectedIndexes()
        if not indexes or indexes[Column.TYPE].data() in self._marker_types or not self._http_api:
            return

        ref = self.get_service_ref(indexes[Column.FAV_ID].data(), indexes[Column.TYPE].data())
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

    def update_audio_tracks(self, tracks):
        self.audio_track_menu.clear()
        current_track = self._player.get_audio_track()
        group = QActionGroup(self.audio_track_menu)
        for t in tracks:
            action = QAction(t[1], self.audio_track_menu)
            action.setCheckable(True)
            track = t[0]
            action.setData(track)
            action.setChecked(current_track == track)
            self.audio_track_menu.addAction(action)
            group.addAction(action)

        group.triggered.connect(self.set_audio_track)

    def update_subtitle_tracks(self, tracks):
        self.subtitle_track_menu.clear()
        group = QActionGroup(self.subtitle_track_menu)
        for t in tracks:
            action = QAction(t[1], self.subtitle_track_menu)
            action.setCheckable(True)
            action.setData(t[0])
            self.subtitle_track_menu.addAction(action)
            group.addAction(action)

        if group.actions():
            group.actions()[0].setChecked(True)
            group.triggered.connect(self.set_subtitle_track)

    def set_audio_track(self, action):
        self._player.set_audio_track(action.data())

    def set_subtitle_track(self, action):
        self._player.set_subtitle_track(action.data())

    def set_aspect_ratio(self, action):
        self._player.set_aspect_ratio(action.data())

    # ********************** EPG *********************** #

    def update_single_epg(self, epg):
        event_list = epg.get("event_list", [])
        self.epg_view.clear_data()
        model = self.epg_view.model()

        for event in event_list:
            title = event.get("e2eventtitle", "")
            desc = event.get("e2eventdescription", "")
            start = int(event.get("e2eventstart", "0"))
            start_time = datetime.fromtimestamp(start)
            end_time = datetime.fromtimestamp(start + int(event.get("e2eventduration", "0")))
            time_header = "{} - {}".format(start_time.strftime("%A, %H:%M"), end_time.strftime("%H:%M"))

            data_item = QStandardItem("Event")
            data_item.setData(event, Qt.UserRole)
            model.appendRow((QStandardItem(title), QStandardItem(time_header), QStandardItem(desc), data_item))

        self.fav_view.setEnabled(True)

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

        self.timer_view.clear_data()
        model = self.timer_view.model()

        for timer in timer_list:
            name = timer.get("e2name", "") or ""
            description = timer.get("e2description", "") or ""
            service_name = timer.get("e2servicename", "") or ""

            start_time = datetime.fromtimestamp(int(timer.get("e2timebegin", "0")))
            end_time = datetime.fromtimestamp(int(timer.get("e2timeend", "0")))
            time_str = "{} - {}".format(start_time.strftime("%A, %H:%M"), end_time.strftime("%H:%M"))

            data_item = QStandardItem("data")
            data_item.setData(timer, Qt.UserRole)
            model.appendRow((QStandardItem(name),
                             QStandardItem(description),
                             QStandardItem(service_name),
                             QStandardItem(time_str),
                             data_item))

    def on_timer_add(self, row):
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_timer_remove(self):
        QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_timer_add_from_event(self, row):
        event = self.epg_view.model().index(row, Column.EPG_EVENT).data(Qt.UserRole)
        timer_dialog = TimerDialog(event, TimerDialog.TimerAction.EVENT)
        if timer_dialog.exec():
            QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    def on_timer_edit(self, row):
        index = self.timer_view.model().index(row, Column.TIMER_DATA)
        timer_dialog = TimerDialog(index.data(Qt.UserRole), TimerDialog.TimerAction.EDIT)
        if timer_dialog.exec():
            QMessageBox.information(self, APP_NAME, self.tr("Not implemented yet!"))

    # ******************** Control ********************* #

    def on_remote_action(self, action):
        self._http_api.send(HttpAPI.Request.REMOTE, action)

    def on_power_action(self, action):
        self._http_api.send(HttpAPI.Request.POWER, action)

    def on_screenshot_all(self, state):
        self._http_api.send(HttpAPI.Request.GRUB, "&mode=all" if self._http_api.is_owif else "&d=")

    def on_screenshot_video(self, state):
        self._http_api.send(HttpAPI.Request.GRUB, "&mode=video" if self._http_api.is_owif else "&v=")

    def on_screenshot_osd(self, state):
        self._http_api.send(HttpAPI.Request.GRUB, "&mode=osd" if self._http_api.is_owif else "&o=")

    def on_action_done(self, req):
        if self.grub_screenshot_box.isChecked():
            self._http_api.send(HttpAPI.Request.GRUB)

    def on_volume_changed(self, value):
        self._http_api.send(HttpAPI.Request.VOL, value)

    def update_screenshot(self, data):
        if "error_code" in data:
            return

        data = data.get("img_data", None)
        if data:
            pix = QPixmap()
            pix.loadFromData(data)
            self.screenshot_label.setPixmap(pix)

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
            self.model_label.setText(model)
            self.e2_version_label.setText(info.get("e2enigmaversion", "N/A"))
            self.image_version_label.setText(info.get("e2imageversion", "N/A"))
        else:
            self.status_bar.showMessage(info_text.format("Disconnected.", ""))
            if all((self.log_action.isChecked(),
                    self.upload_tool_button.isEnabled(),
                    self.upload_tool_button.isEnabled())):
                reason = info.get("reason", None)
                self.log_text_browser.append(reason) if reason else None

        if self.current_page is Page.CONTROL:
            self._http_api.send(HttpAPI.Request.SIGNAL)

    def update_signal(self, sig):
        self.snr_progress_bar.setValue(int(sig.get("e2snr", "0 %").strip().rstrip("%N/A") or 0))
        self.ber_progress_bar.setValue(int((sig.get("e2ber", None) or "").strip().rstrip("N/A") or 0))
        self.agc_progress_bar.setValue(int(sig.get("e2acg", "0 %").strip().rstrip("%N/A") or 0))

    def on_app_exit(self, state):
        self.close()

    def show_error_dialog(self, msg):
        QMessageBox.critical(self, APP_NAME, msg)

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
