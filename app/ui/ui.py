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


""" Core UI module. """
from enum import IntEnum

from PyQt5 import QtCore, QtGui, QtWidgets, uic

from app.ui.settings import UI_PATH, IS_LINUX
from app.ui.views import *


class Page(IntEnum):
    """ Main stack widget page. """
    BOUQUETS = 0
    SAT = 1
    PICONS = 2
    EPG = 3
    TIMER = 4
    FTP = 5
    LOGO = 6
    CONTROL = 7


class MainUiWindow(QtWidgets.QMainWindow):
    """ Base UI class.

        Based on code from the PyQt5 UI generator.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Loading GUI skeleton from .ui file.
        uic.loadUi(f"{UI_PATH}main.ui", self)
        # ******************** Views ******************** #
        self.services_view = ServicesView(self.services_group_box)
        self.services_group_box_layout.insertWidget(1, self.services_view)
        # FAV
        self.fav_view = FavView(self.fav_group_box)
        self.fav_layout.insertWidget(1, self.fav_view)
        # Bouquets
        self.bouquets_view = BouquetsView(self.bouquets_group_box)
        self.bouquets_layout.insertWidget(1, self.bouquets_view)
        # Satellites
        self.satellite_view = SatelliteView(self.satellites_group_box)
        self.satellite_view.setObjectName("satellite_view")
        self.satellite_group_box_layout.insertWidget(1, self.satellite_view)
        # Transponders
        self.transponder_view = TransponderView(self.transponders_box)
        self.transponder_box_layout.insertWidget(1, self.transponder_view)
        # Picons
        self.picon_src_view = PiconView(self.picon_src_box)
        self.picon_src_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.picon_src_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.picon_src_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.picon_src_layout.addWidget(self.picon_src_view)

        self.picon_dst_view = PiconDstView(self.picon_dst_box)
        self.picon_dst_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.picon_dst_layout.addWidget(self.picon_dst_view)
        # EPG
        self.epg_view = EpgView(self.epg_group_box)
        self.epg_group_box_layout.addWidget(self.epg_view)
        self.epg_page_layout.addWidget(self.epg_group_box, 0, 0, 1, 1)
        # Timers
        self.timer_view = TimerView(self.timer_group_box)
        self.timer_view_layout.addWidget(self.timer_view)
        # FTP
        self.ftp_src_view = FtpView(self.ftp_src_group_box)
        self.ftp_src_group_box_layout.addWidget(self.ftp_src_view)
        self.ftp_dest_view = FileView(self.ftp_dest_group_box)
        self.ftp_dest_group_box_layout.addWidget(self.ftp_dest_view)
        # ******************* Streams Playback ******************* #
        self.central_widget = self.centralWidget()
        # Media widget.
        self.media_widget = MediaView(self.media_frame)
        self.media_layout.insertWidget(0, self.media_widget)
        # Extra options.
        self.media_widget.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors)
        self.media_widget.setAttribute(QtCore.Qt.WA_NativeWindow)
        # Streams button. Used as an intermediate (state) widget.
        self.streams_tool_button = QtWidgets.QToolButton(self.central_widget)
        self.streams_tool_button.setCheckable(True)
        self.streams_tool_button.setAutoExclusive(True)
        self.streams_tool_button.setVisible(False)
        self.streams_tool_button.setObjectName("streams_tool_button")
        self.header_layout.addWidget(self.streams_tool_button)
        # ******************** Menu bar ******************** #
        self.file_menu_action = self.file_menu.menuAction()
        self.view_menu_action = self.view_menu.menuAction()
        self.backup_menu_action = self.backup_menu.menuAction()

        self.playback_menu_action = self.playback_menu.menuAction()
        self.audio_menu_action = self.audio_menu.menuAction()
        self.video_menu_action = self.video_menu.menuAction()
        self.subtitle_menu_action = self.subtitle_menu.menuAction()

        self.default_ratio_action = QtWidgets.QAction(self.aspect_ratio_menu)
        self.default_ratio_action.setCheckable(True)
        self.aspect_ratio_menu.addAction(self.default_ratio_action)
        # ******************** Popups ******************** #
        # FAV tools menu.
        self.fav_tools_menu = QtWidgets.QMenu("IPTV", self.fav_menu_button)
        self.add_stream_action = QtWidgets.QAction("Add IPTV or stream service", self.fav_tools_menu)
        self.add_stream_action.setIcon(QtGui.QIcon.fromTheme("emblem-shared"))
        self.fav_tools_menu.addAction(self.add_stream_action)
        self.import_m3u_action = QtWidgets.QAction("Import *m3u", self.fav_tools_menu)
        self.import_m3u_action.setIcon(QtGui.QIcon.fromTheme("insert-link"))
        self.fav_tools_menu.addAction(self.import_m3u_action)
        self.fav_menu_button.setMenu(self.fav_tools_menu)
        # Picons.
        self.picon_dst_remove_button.setMenu(self.picon_dst_view.context_menu)
        # Translation
        self.retranslate_ui(self)
        # Startup
        self.stacked_widget.setCurrentIndex(0)
        self.log_text_browser.setVisible(False)
        self.media_frame.setVisible(False)
        self.playback_menu_action.setVisible(False)
        self.audio_menu_action.setVisible(False)
        self.video_menu_action.setVisible(False)
        self.subtitle_menu_action.setVisible(False)
        # Setting the stretch factor to proportional widgets resize
        self.main_splitter.setStretchFactor(0, 4)
        self.main_splitter.setStretchFactor(1, 5)
        self.satellite_splitter.setStretchFactor(0, 1)  # -> index, stretch factor
        self.satellite_splitter.setStretchFactor(1, 2)
        # Current stack page
        self.current_page = Page.BOUQUETS
        # Actions.
        self.alternate_layout_action.toggled['bool'].connect(self.set_layout)
        bq_display_group = QtWidgets.QActionGroup(self.bouquets_display_menu)
        bq_display_group.addAction(self.bq_display_vertical_action)
        bq_display_group.addAction(self.bq_display_horizontally_action)
        bq_display_group.triggered.connect(self.on_bouquets_display_mode_changed)
        QtCore.QMetaObject.connectSlotsByName(self)
        # Toolbar.
        self.bouquet_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, Page.BOUQUETS))
        self.satellite_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, Page.SAT))
        self.picon_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, Page.PICONS))
        self.epg_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, Page.EPG))
        self.timer_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, Page.TIMER))
        self.ftp_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, Page.FTP))
        self.logo_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, Page.LOGO))
        self.control_tool_button.toggled.connect(lambda s: self.on_stack_page_changed(s, Page.CONTROL))
        # Filtering.
        self.service_filter_edit.textChanged.connect(self.services_view.model().set_filter_text)
        self.satellite_filter_edit.textChanged.connect(self.satellite_view.model().set_filter_text)
        self.transponders_filter_edit.textChanged.connect(self.transponder_view.model().set_filter_text)
        self.picon_src_filter_edit.textChanged.connect(self.picon_src_view.model().filter)
        self.picon_dest_filter_edit.textChanged.connect(self.picon_dst_view.model().filter)
        # Stack pages.
        self.stacked_widget.currentChanged.connect(self.on_current_page_changed)
        # Styled elements.
        self.init_styled()
        # Playback.
        self.init_playback_elements()
        # Disabled items!!!
        self.logo_tool_button.setVisible(False)
        self.ftp_tool_button.setVisible(False)
        self.picon_src_box.setVisible(False)
        self.import_action.setVisible(False)
        self.filter_free_button.setVisible(False)
        self.filter_type_combo_box.setVisible(False)
        self.filter_pos_combo_box.setVisible(False)
        self.not_in_bq_filter_button.setVisible(False)
        self.satellite_update_tool_button.setVisible(False)
        self.ftp_action.setVisible(False)
        self.logo_action.setVisible(False)

    def init_styled(self):
        self.red_button.setStyleSheet("background-color: red; border: 2px solid red")
        self.green_button.setStyleSheet("background-color: green; border: 2px solid green")
        self.yellow_button.setStyleSheet("background-color: yellow; border: 2px solid yellow")
        self.blue_button.setStyleSheet("background-color: blue; border: 2px solid blue")
        # Button icons.
        if not IS_LINUX:
            style = self.style()
            self.fav_menu_button.setIcon(style.standardIcon(style.SP_DriveNetIcon))
            # Player
            self.media_play_tool_button.setIcon(style.standardIcon(style.SP_MediaPlay))
            self.media_stop_tool_button.setIcon(style.standardIcon(style.SP_MediaStop))
            self.media_full_tool_button.setIcon(style.standardIcon(style.SP_TitleBarMaxButton))
            # Control
            self.media_prev_button.setIcon(style.standardIcon(style.SP_MediaSeekBackward))
            self.media_play_button.setIcon(style.standardIcon(style.SP_MediaPlay))
            self.media_stop_button.setIcon(style.standardIcon(style.SP_MediaStop))
            self.media_next_button.setIcon(style.standardIcon(style.SP_MediaSeekForward))

            info_pix = style.standardIcon(style.SP_MessageBoxInformation).pixmap(QtCore.QSize(16, 16))
        else:
            info_pix = QtGui.QIcon.fromTheme("document-properties").pixmap(QtCore.QSize(16, 16))
        # Info labels.
        self.fav_info_label.setPixmap(info_pix)
        self.bouquets_info_label.setPixmap(info_pix)
        self.services_info_label.setPixmap(info_pix)
        self.satellite_info_label.setPixmap(info_pix)
        self.transponder_info_label.setPixmap(info_pix)

    def init_playback_elements(self):
        # Aspect ratio.
        ratios = ("16:9", "4:3", "1:1", "16:10", "5:4")
        group = QtWidgets.QActionGroup(self.aspect_ratio_menu)
        group.addAction(self.default_ratio_action)
        self.default_ratio_action.setChecked(True)
        group.triggered.connect(self.set_aspect_ratio)

        for ratio in ratios:
            action = QtWidgets.QAction(ratio, self.aspect_ratio_menu)
            action.setCheckable(True)
            action.setData(ratio)
            self.aspect_ratio_menu.addAction(action)
            group.addAction(action)

        self.streams_tool_button.toggled.connect(self.set_menu_elements_visibility)
        self.streams_tool_button.toggled.connect(self.set_playback_state)
        self.close_playback_action.triggered.connect(self.bouquet_tool_button.toggle)

    @QtCore.pyqtSlot(bool)
    def set_menu_elements_visibility(self, visible):
        self.playback_menu_action.setVisible(visible)
        self.audio_menu_action.setVisible(visible)
        self.video_menu_action.setVisible(visible)
        self.subtitle_menu_action.setVisible(visible)
        self.file_menu_action.setVisible(not visible)
        self.view_menu_action.setVisible(not visible)
        self.file_menu_action.setVisible(not visible)
        self.backup_menu_action.setVisible(not visible)

    def set_playback_state(self, state):
        if not state:
            self.media_stop_tool_button.click()
        else:
            self.base_splitter.setStretchFactor(0, 7)
            self.base_splitter.setStretchFactor(1, 3)

        self.media_frame.setVisible(state)
        self.stacked_widget.setVisible(not state)

    # ******************** Handlers ******************** #

    def on_stack_page_changed(self, state, p_num):
        if state:
            self.stacked_widget.setCurrentIndex(p_num)
            self.fav_splitter.setVisible(p_num not in (Page.SAT, Page.FTP, Page.LOGO, Page.CONTROL))
            is_file_action = p_num in (Page.BOUQUETS, Page.SAT, Page.PICONS)
            self.open_action.setEnabled(is_file_action)
            self.import_action.setEnabled(is_file_action)
            self.extract_action.setEnabled(is_file_action)
            self.save_action.setEnabled(is_file_action)
            self.save_as_action.setEnabled(is_file_action)
            self.upload_tool_button.setEnabled(is_file_action)

    def on_current_page_changed(self, index):
        page = Page(index)
        self.current_page = page
        if page is Page.SAT:
            self.on_satellite_page_show()
        elif page is Page.PICONS:
            self.on_picon_page_show()
        elif page is Page.TIMER:
            self.on_timer_page_show()

    def set_layout(self, alt):
        """ Sets main elements layout type. """
        index = int(not alt)
        self.base_splitter.insertWidget(index, self.main_frame)
        self.main_splitter.insertWidget(index, self.fav_splitter)
        self.control_horizontal_layout.insertWidget(index, self.remote_controller_box)
        if self.bq_display_horizontally_action.isChecked():
            self.fav_splitter.insertWidget(index, self.fav_group_box)
            self.fav_splitter.insertWidget(index, self.bouquets_group_box)

    def on_bouquets_display_mode_changed(self, action):
        """ Sets  bouquets and favorites list display position. """
        vertical = self.bq_display_vertical_action.isChecked()
        self.fav_splitter.setOrientation(QtCore.Qt.Vertical if vertical else QtCore.Qt.Horizontal)
        if self.alternate_layout_action.isChecked():
            index = int(not vertical)
            self.fav_splitter.insertWidget(index, self.bouquets_group_box)
            self.fav_splitter.insertWidget(index, self.fav_group_box)

    def retranslate_ui(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("MainWindow", "E2Toolkit"))
        # Tool bar.
        self.profile_combo_box.setToolTip(_translate("MainWindow", "Profile"))
        self.download_tool_button.setToolTip(_translate("MainWindow", "Receive files from the receiver"))
        self.download_tool_button.setText(_translate("MainWindow", "Receive"))
        self.upload_tool_button.setToolTip(_translate("MainWindow", "Send files to the receiver"))
        self.upload_tool_button.setText(_translate("MainWindow", "Send"))
        self.bouquet_tool_button.setText(_translate("MainWindow", "Bouquets"))
        self.satellite_tool_button.setText(_translate("MainWindow", "Satellites"))
        self.picon_tool_button.setText(_translate("MainWindow", "Picons"))
        self.epg_tool_button.setText(_translate("MainWindow", "EPG"))
        self.timer_tool_button.setText(_translate("MainWindow", "Timer"))
        self.ftp_tool_button.setText(_translate("MainWindow", "FTP"))
        self.logo_tool_button.setText(_translate("MainWindow", "Logo"))
        self.control_tool_button.setText(_translate("MainWindow", "Control"))
        # Services.
        self.services_group_box.setTitle(_translate("MainWindow", "Services"))
        self.filter_free_button.setToolTip(_translate("MainWindow", "Only free"))
        self.filter_free_button.setText(_translate("MainWindow", " Free"))
        self.service_filter_edit.setToolTip(_translate("MainWindow", "RegExp -> Name|Package|Type|Pos1|Pos2 -> etc."))
        self.service_filter_edit.setPlaceholderText(_translate("MainWindow", "Filter..."))
        self.service_search_edit.setToolTip(_translate("MainWindow", "Search text"))
        self.service_search_edit.setPlaceholderText(_translate("MainWindow", "Search..."))
        self.tv_label.setText(_translate("MainWindow", "TV:"))
        self.radio_label.setText(_translate("MainWindow", "Radio:"))
        self.data_label.setText(_translate("MainWindow", "Data:"))
        # Satellites page.
        self.satellites_group_box.setTitle(_translate("MainWindow", "Satellites"))
        self.satellite_update_tool_button.setText(_translate("MainWindow", "Update"))
        self.satellite_filter_edit.setPlaceholderText(_translate("MainWindow", "Filter..."))
        self.transponders_box.setTitle(_translate("MainWindow", "Transponders"))
        self.transponders_filter_edit.setPlaceholderText(_translate("MainWindow", "Filter..."))
        # Picons page.
        self.picon_src_box.setTitle(_translate("MainWindow", "Source"))
        self.picon_dst_box.setTitle(_translate("MainWindow", "Picons"))
        self.picon_src_filter_edit.setPlaceholderText(_translate("MainWindow", "Filter..."))
        self.picon_dest_filter_edit.setPlaceholderText(_translate("MainWindow", "Filter..."))
        self.picon_dst_remove_button.setText(_translate("MainWindow", "Remove"))
        # Streams page.
        self.media_play_tool_button.setText(_translate("MainWindow", "Play"))
        self.media_stop_tool_button.setText(_translate("MainWindow", "Stop"))
        self.media_full_tool_button.setText(_translate("MainWindow", "Fullscreen"))
        # EPG page.
        self.epg_group_box.setTitle(_translate("MainWindow", "EPG"))
        self.epg_search_edit.setPlaceholderText(_translate("MainWindow", "Search..."))
        # Timer page.
        self.timer_group_box.setTitle(_translate("MainWindow", "Timers"))
        self.timer_search_edit.setPlaceholderText(_translate("MainWindow", "Search..."))
        self.timer_add_button.setText(_translate("MainWindow", "Add"))
        self.timer_remove_button.setText(_translate("MainWindow", "Remove"))
        # FTP page.
        self.ftp_src_group_box.setTitle(_translate("MainWindow", "FTP"))
        self.ftp_src_status_label.setText(_translate("MainWindow", "Status:"))
        self.ftp_dest_group_box.setTitle(_translate("MainWindow", "PC"))
        self.ftp_dest_status_label.setText(_translate("MainWindow", "Status:"))
        # Control page.
        self.power_control_box.setTitle(_translate("MainWindow", "Power"))
        self.power_standby_button.setText(_translate("MainWindow", "Standby"))
        self.power_wake_up_button.setText(_translate("MainWindow", "Wake Up"))
        self.power_reboot_button.setText(_translate("MainWindow", "Reboot"))
        self.power_restart_gui_button.setText(_translate("MainWindow", "Restart GUI"))
        self.power_shutdown_button.setText(_translate("MainWindow", "Shutdown"))
        self.remote_controller_box.setTitle(_translate("MainWindow", "Remote"))
        self.control_volume_dial.setToolTip(_translate("MainWindow", "Volume"))
        self.media_play_button.setText(_translate("MainWindow", "PLAY"))
        self.media_stop_button.setText(_translate("MainWindow", "STOP"))
        self.media_prev_button.setText(_translate("MainWindow", "PREV"))
        self.media_next_button.setText(_translate("MainWindow", "NEXT"))
        self.grub_screenshot_button.setText(_translate("MainWindow", "Grab screenshot"))
        self.screenshot_control_box.setTitle(_translate("MainWindow", "Screenshot"))
        self.screenshot_all_button.setText(_translate("MainWindow", "All"))
        self.screenshot_video_button.setText(_translate("MainWindow", "Video"))
        self.screenshot_osd_button.setText(_translate("MainWindow", "OSD"))
        self.control_info_group_box.setTitle(_translate("MainWindow", "Box Info"))
        self.model_info_label.setText(_translate("MainWindow", "Model:"))
        self.e2_version_info_label.setText(_translate("MainWindow", "Enigma2 version:"))
        self.image_version_info_label.setText(_translate("MainWindow", "Image version:"))
        self.signal_box.setTitle(_translate("MainWindow", "Signal level"))
        self.snr_label.setText(_translate("MainWindow", "SNR:"))
        self.ber_label.setText(_translate("MainWindow", "BER:"))
        self.agc_label.setText(_translate("MainWindow", "AGC:"))
        # FAV
        self.fav_group_box.setTitle(_translate("MainWindow", "Bouquet services"))
        self.bq_service_search_edit.setPlaceholderText(_translate("MainWindow", "Search..."))
        self.bouquets_group_box.setTitle(_translate("MainWindow", "Bouquets"))
        self.add_bouquet_button.setToolTip(_translate("MainWindow", "Add"))
        self.add_bouquet_button.setText(_translate("MainWindow", "Add"))
        # Menu bar.
        self.file_menu.setTitle(_translate("MainWindow", "File"))
        self.view_menu.setTitle(_translate("MainWindow", "View"))
        self.backup_menu.setTitle(_translate("MainWindow", "Backup"))
        self.settings_menu.setTitle(_translate("MainWindow", "Settings"))
        self.language_menu.setTitle(_translate("MainWindow", "Language"))
        self.help_menu.setTitle(_translate("MainWindow", "Help"))
        self.tools_menu.setTitle(_translate("MainWindow", "Tools"))
        self.open_action.setText(_translate("MainWindow", "Open"))
        self.open_action.setShortcut(_translate("MainWindow", "Ctrl+O"))
        self.save_action.setShortcut(_translate("MainWindow", "Ctrl+S"))
        self.exit_action.setText(_translate("MainWindow", "Exit"))
        self.exit_action.setShortcut(_translate("MainWindow", "Ctrl+Q"))
        self.backup_restore_action.setText(_translate("MainWindow", "Restore..."))
        self.settings_action.setText(_translate("MainWindow", "Settings..."))
        self.view_menu.setTitle(_translate("MainWindow", "View"))
        self.tools_menu.setTitle(_translate("MainWindow", "Tools"))
        self.playback_menu.setTitle(_translate("MainWindow", "Playback"))
        self.close_playback_action.setText(_translate("MainWindow", "Close Playback"))
        self.save_action.setText(_translate("MainWindow", "Save"))
        self.save_as_action.setText(_translate("MainWindow", "Save As..."))
        self.audio_menu.setTitle(_translate("MainWindow", "Audio"))
        self.audio_track_menu.setTitle(_translate("MainWindow", "Audio Track"))
        self.video_menu.setTitle(_translate("MainWindow", "Video"))
        self.aspect_ratio_menu.setTitle(_translate("MainWindow", "Aspect ratio"))
        self.default_ratio_action.setText(_translate("MainWindow", "Default"))
        self.subtitle_menu.setTitle(_translate("MainWindow", "Subtitle"))
        self.subtitle_track_menu.setTitle(_translate("MainWindow", "Subtitle Track"))
        self.import_action.setText(_translate("MainWindow", "Import"))
        self.extract_action.setText(_translate("MainWindow", "Extract..."))
        self.about_action.setText(_translate("MainWindow", "About"))
        self.english_lang_action.setText(_translate("MainWindow", "English"))
        self.bouquets_action.setText(_translate("MainWindow", "Bouquets"))
        self.satellites_action.setText(_translate("MainWindow", "Satellites"))
        self.picons_action.setText(_translate("MainWindow", "Picons"))
        self.epg_action.setText(_translate("MainWindow", "EPG"))
        self.timer_action.setText(_translate("MainWindow", "Timer"))
        self.logo_action.setText(_translate("MainWindow", "Logo"))
        self.log_action.setText(_translate("MainWindow", "Logs"))
        # ******************** Popups and menu. ******************** #
        # FAV tools menu.
        self.fav_tools_menu.setTitle(_translate("MainWindow", "Tools"))
        self.add_stream_action.setText(_translate("MainWindow", "Add IPTV or stream service"))
        self.import_m3u_action.setText(_translate("MainWindow", "Import *m3u"))

    # Pages
    def on_satellite_page_show(self):
        pass

    def on_picon_page_show(self):
        pass

    def on_timer_page_show(self):
        pass

    # Playback
    def set_aspect_ratio(self, action):
        pass
