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


__all__ = ["TimerDialog",
           "ServiceDialog",
           "IptvServiceDialog",
           "BackupDialog",
           "SatelliteDialog",
           "TransponderDialog",
           "InputDialog"]

import zipfile
from datetime import datetime
from enum import IntEnum
from urllib.parse import unquote, quote

from PyQt5 import QtWidgets, QtCore, QtGui, uic

from app.commons import log, APP_NAME
from app.enigma.ecommons import Pids, Flag, Service, BqServiceType, FEC, SYSTEM, POLARIZATION, MODULATION, PLS_MODE
from app.satellites.satxml import get_key_by_value
from app.streams.iptv import StreamType, get_fav_id
from app.ui.models import ServiceTypeModel
from app.ui.uicommons import UI_PATH
from app.ui.views import BackupFileView


class TimerDialog(QtWidgets.QDialog):
    class TimerAction(IntEnum):
        ADD = 0
        EVENT = 1
        EDIT = 2

    class TimerActionModel(QtGui.QStandardItemModel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for t in (self.tr("Record"), "0"), (self.tr("Zap"), "1"):
                self.appendRow((QtGui.QStandardItem(t[0]), QtGui.QStandardItem(t[1])))

    class TimerAfterEventModel(QtGui.QStandardItemModel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for a in ((self.tr("Do Nothing"), "0"),
                      (self.tr("Standby"), "1"),
                      (self.tr("Shut down"), "2"),
                      (self.tr("Auto"), "3")):
                self.appendRow((QtGui.QStandardItem(a[0]), QtGui.QStandardItem(a[1])))

    def __init__(self, data, action, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(f"{UI_PATH}timer_dialog.ui", self)
        # Models.
        self.timer_action_combo_box.setModel(self.TimerActionModel(self.timer_action_combo_box))
        self.timer_after_event_combo_box.setModel(self.TimerAfterEventModel(self.timer_after_event_combo_box))

        self.retranslate_ui()

        self._data = data or {}
        self._action = action
        self._request = ""
        self.init_timer_data()

    @property
    def timer_data(self):
        return self._data

    @property
    def request(self):
        return self._request

    def init_timer_data(self):
        if self._action is self.TimerAction.ADD:
            self.init_add()
        elif self._action is self.TimerAction.EDIT:
            self.init_edit()
        elif self._action is self.TimerAction.EVENT:
            self.init_event()

    def init_add(self):
        self.timer_service_edit.setText(self._data.get("e2servicename", ""))
        self.timer_ref_edit.setText(self._data.get("e2servicereference", ""))
        date = datetime.now()
        self.timer_begins_edit.setDateTime(date)
        self.timer_ends_edit.setDateTime(date)
        self.timer_event_id_edit.setText("")

    def init_edit(self):
        self.timer_enable_button.setChecked(self._data.get("e2disabled", "0") == "0")
        self.timer_name_edit.setText(self._data.get("e2name", "") or "")
        self.timer_description_edit.setText(self._data.get("e2description", "") or "")
        self.timer_service_edit.setText(self._data.get("e2servicename", "") or "")
        self.timer_ref_edit.setText(self._data.get("e2servicereference", ""))
        self.timer_event_id_edit.setText(self._data.get("e2eit", ""))
        self.timer_begins_edit.setDateTime(datetime.fromtimestamp(int(self._data.get("e2timebegin", "0"))))
        self.timer_ends_edit.setDateTime(datetime.fromtimestamp(int(self._data.get("e2timeend", "0"))))
        self.timer_action_combo_box.setCurrentIndex(int(self._data.get("e2justplay", "0")))
        self.timer_after_event_combo_box.setCurrentIndex(int(self._data.get("e2afterevent", "0")))
        # Days
        self.set_repetition_flags(int(self._data.get("e2repeated", "0")))

    def init_event(self):
        self.timer_name_edit.setText(self._data.get("e2eventtitle", "") or "")
        self.timer_description_edit.setText(self._data.get("e2eventdescription", "") or "")
        self.timer_service_edit.setText(self._data.get("e2eventservicename", "") or "")
        self.timer_ref_edit.setText(self._data.get("e2eventservicereference", ""))
        self.timer_event_id_edit.setText(self._data.get("e2eventid", ""))
        self.timer_action_combo_box.setCurrentIndex(1)
        self.timer_after_event_combo_box.setCurrentIndex(3)
        # Time
        start_time = int(self._data.get("e2eventstart", "0"))
        end_time = start_time + int(self._data.get("e2eventduration", "0"))
        self.timer_begins_edit.setDateTime(datetime.fromtimestamp(start_time))
        self.timer_ends_edit.setDateTime(datetime.fromtimestamp(end_time))

    def accept(self):
        if QtWidgets.QMessageBox.question(self, APP_NAME, self.tr("Are you sure?")) != QtWidgets.QMessageBox.Yes:
            return

        self._request = self.get_request()
        super().accept()

    def get_repetition_flags(self):
        """ Returns flags for repetition. """
        day_flags = 0
        for i, box in enumerate((self.timer_mo_check_box, self.timer_tu_check_box, self.timer_we_check_box,
                                 self.timer_th_check_box, self.timer_fr_check_box, self.timer_sa_check_box,
                                 self.timer_su_check_box)):

            if box.isChecked():
                day_flags = day_flags | (1 << i)

        return day_flags

    def set_repetition_flags(self, flags):
        for i, box in enumerate((self.timer_mo_check_box, self.timer_tu_check_box, self.timer_we_check_box,
                                 self.timer_th_check_box, self.timer_fr_check_box, self.timer_sa_check_box,
                                 self.timer_su_check_box)):
            box.setChecked(flags & 1 == 1)
            flags = flags >> 1

    def get_request(self):
        """ Constructs str representation of add/update request. """
        args = []
        t_data = self.get_timer_data()
        s_ref = quote(t_data.get("sRef", ""))

        if self._action is self.TimerAction.EVENT:
            args.append(f"timeraddbyeventid?sRef={s_ref}")
            args.append(f"eventid={t_data.get('eit', '0')}")
            args.append(f"justplay={t_data.get('justplay', '')}")
            args.append(f"tags={''}")
        else:
            if self._action is self.TimerAction.ADD:
                args.append(f"timeradd?sRef={s_ref}")
                args.append(f"deleteOldOnSave={0}")
            elif self._action is self.TimerAction.EDIT:
                args.append(f"timerchange?sRef={s_ref}")
                args.append(f"channelOld={s_ref}")
                args.append(f"beginOld={self._data.get('e2timebegin', '0')}")
                args.append(f"endOld={self._data.get('e2timeend', '0')}")
                args.append(f"deleteOldOnSave={1}")

            args.append(f"begin={t_data.get('begin', '')}")
            args.append(f"end={t_data.get('end', '')}")
            args.append(f"name={quote(t_data.get('name', ''))}")
            args.append(f"description={quote(t_data.get('description', ''))}")
            args.append(f"tags={''}")
            args.append(f"eit={'0'}")
            args.append(f"disabled={t_data.get('disabled', '1')}")
            args.append(f"justplay={t_data.get('justplay', '1')}")
            args.append(f"afterevent={t_data.get('afterevent', '0')}")
            args.append(f"repeated={self.get_repetition_flags()}")

        return "&".join(args)

    def get_timer_data(self):
        """ Returns timer data as a dict. """
        return {"sRef": self.timer_ref_edit.text(),
                "begin": int(self.timer_begins_edit.dateTime().toPyDateTime().timestamp()),
                "end": int(self.timer_ends_edit.dateTime().toPyDateTime().timestamp()),
                "name": self.timer_name_edit.text(),
                "description": self.timer_description_edit.text(),
                "dirname": self.timer_location_combo_box.currentText(),
                "eit": self.timer_event_id_edit.text(),
                "disabled": int(not self.timer_enable_button.isChecked()),
                "justplay": self.timer_action_combo_box.currentIndex(),
                "afterevent": self.timer_after_event_combo_box.currentIndex(),
                "repeated": self.get_repetition_flags()}

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("timer_dialog", "E2Toolkit [Timer]"))
        self.timer_enable_button.setText(_translate("timer_dialog", "Enabled"))
        self.timer_name_label.setText(_translate("timer_dialog", "Name:"))
        self.timer_description_label.setText(_translate("timer_dialog", "Description:"))
        self.timer_service_label.setText(_translate("timer_dialog", "Service:"))
        self.timer_service_ref_label.setText(_translate("timer_dialog", "Reference:"))
        self.timer_event_id_label.setText(_translate("timer_dialog", "Event ID:"))
        self.timer_begins_label.setText(_translate("timer_dialog", "Begins:"))
        self.timer_ends_label.setText(_translate("timer_dialog", "Ends:"))
        self.timer_repeated_label.setText(_translate("timer_dialog", "Repeated:"))
        self.timer_th_label.setText(_translate("timer_dialog", "Th"))
        self.timer_su_label.setText(_translate("timer_dialog", "Su"))
        self.timer_tu_label.setText(_translate("timer_dialog", "Tu"))
        self.timer_sa_label.setText(_translate("timer_dialog", "Sa"))
        self.timer_mo_label.setText(_translate("timer_dialog", "Mo"))
        self.timer_we_label.setText(_translate("timer_dialog", "We"))
        self.timer_fr_label.setText(_translate("timer_dialog", "Fr"))
        self.timer_action_label.setText(_translate("timer_dialog", "Action:"))
        self.timer_after_event_label.setText(_translate("timer_dialog", "After event:"))
        self.timer_location_label.setText(_translate("timer_dialog", "Location:"))


class ServiceDialog(QtWidgets.QDialog):
    def __init__(self, service, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(f"{UI_PATH}service_dialog.ui", self)
        # Types.
        self.type_combo_box.setModel(ServiceTypeModel(self.type_combo_box))
        self.type_combo_box.currentTextChanged.connect(self.update_reference_entry)
        self.sid_edit.textChanged.connect(self.update_reference_entry)
        # Value validation.
        self.sid_edit.setValidator(QtGui.QIntValidator(self.sid_edit))
        self.video_pid_edit.setValidator(QtGui.QIntValidator(self.video_pid_edit))
        self.audio_pid_edit.setValidator(QtGui.QIntValidator(self.audio_pid_edit))
        self.teletext_pid_edit.setValidator(QtGui.QIntValidator(self.teletext_pid_edit))
        self.pcr_pid_edit.setValidator(QtGui.QIntValidator(self.pcr_pid_edit))
        self.ac3_pid_edit.setValidator(QtGui.QIntValidator(self.ac3_pid_edit))
        self.ac3p_pid_edit.setValidator(QtGui.QIntValidator(self.ac3p_pid_edit))
        self.acc_pid_edit.setValidator(QtGui.QIntValidator(self.acc_pid_edit))
        self.he_acc_pid_edit.setValidator(QtGui.QIntValidator(self.he_acc_pid_edit))
        # Disabled
        self.ac3_pid_edit.setVisible(False)
        self.ac3_label.setVisible(False)
        self.ac3p_pid_edit.setVisible(False)
        self.ac3p_label.setVisible(False)
        self.acc_pid_edit.setVisible(False)
        self.acc_label.setVisible(False)
        self.he_acc_pid_edit.setVisible(False)
        self.he_acc_label.setVisible(False)

        self.retranslate_ui()
        # Data init
        self._service = service
        self._tid = 0
        self._nid = 0
        self._namespace = 0
        self.init_service_data()

    @property
    def service(self):
        return self._service

    def init_service_data(self):
        """ Service data initialisation. """
        self.name_edit.setText(self._service.name)
        self.package_edit.setText(self._service.package)
        self.sid_edit.setText(str(int(self._service.ssid, 16)))
        self.type_combo_box.setCurrentText(self._service.service_type)

        flags = self._service.flags_cas
        if flags:
            flags = flags.split(",")
            self.init_flags(flags)
            self.init_pids(flags)
            self.init_cas(flags)
        # Transponder
        data = self._service.data_id.split(":")
        self._tid = int(data[2], 16)
        self._nid = int(data[3], 16)
        self._namespace = int(data[1], 16)
        self.update_reference_entry()

    def init_flags(self, flags):
        f_flags = list(filter(lambda x: x.startswith("f:"), flags))
        if f_flags:
            value = Flag.parse(f_flags[0])
            self.keep_flag_check_box.setChecked(Flag.is_keep(value))
            self.hide_flag_check_box.setChecked(Flag.is_hide(value))
            self.use_pids_flag_check_box.setChecked(Flag.is_pids(value))
            self.new_flag_check_box.setChecked(Flag.is_new(value))

    def init_cas(self, flags):
        cas = list(filter(lambda x: x.startswith("C:"), flags))
        if cas:
            self.caids_edit.setText(",".join(cas))

    def init_pids(self, flags):
        pids = list(filter(lambda x: x.startswith("c:"), flags))
        if pids:
            extra_pids = []
            for pid in pids:
                if pid.startswith(Pids.VIDEO.value):
                    self.video_pid_edit.setText(str(int(pid[4:], 16)))
                elif pid.startswith(Pids.AUDIO.value):
                    self.audio_pid_edit.setText(str(int(pid[4:], 16)))
                elif pid.startswith(Pids.TELETEXT.value):
                    self.teletext_pid_edit.setText(str(int(pid[4:], 16)))
                elif pid.startswith(Pids.PCR.value):
                    self.pcr_pid_edit.setText(str(int(pid[4:], 16)))
                elif pid.startswith(Pids.AC3.value):
                    self.ac3_pid_edit.setText(str(int(pid[4:], 16)))
                elif pid.startswith(Pids.VIDEO_TYPE.value):
                    extra_pids.append(pid)
                elif pid.startswith(Pids.AUDIO_CHANNEL.value):
                    extra_pids.append(pid)
                elif pid.startswith(Pids.BIT_STREAM_DELAY.value):
                    # str(int(pid[4:], 16)))
                    pass
                elif pid.startswith(Pids.PCM_DELAY.value):
                    # str(int(pid[4:], 16))
                    pass
                elif pid.startswith(Pids.SUBTITLE.value):
                    extra_pids.append(pid)
                else:
                    extra_pids.append(pid)

            self.extra_edit.setText(",".join(extra_pids))

    def accept(self):
        if not self.is_data_correct():
            return

        data = self.ref_edit.text().split(":")
        flags = self.get_service_flags()
        name = self.name_edit.text()
        package = self.package_edit.text()
        ssid = f"{int(self.sid_edit.text()):04x}"
        fav_id = f"{data[3]}:{data[4]}:{data[5]}:{data[6]}"
        picon_id = f"1_0_{data[2]}_{data[3]}_{data[4]}_{data[5]}_{data[6]}_0_0_0.png"
        namespace, tid, nid = int(data[6], 16), int(data[4], 16), int(data[5], 16)
        s_type = int(data[2], 16)
        data_id = f"{ssid}:{namespace:08x}:{tid:04x}:{nid:04x}:{s_type}:0"
        s_type = self.type_combo_box.currentText()
        self._service = self._service._replace(flags_cas=flags, picon_id=picon_id, name=name, package=package,
                                               service_type=s_type, ssid=ssid, data_id=data_id, fav_id=fav_id)

        super().accept()

    def get_service_flags(self):
        """ Returns service flags. """
        flags = [f"p:{self.package_edit.text()}"]
        # CAS.
        cas = self.caids_edit.text()
        if cas:
            flags.append(cas)
        # Pids.
        video_pid = self.video_pid_edit.text()
        if video_pid:
            flags.append(f"{Pids.VIDEO.value}{int(video_pid):04x}")
        audio_pid = self.audio_pid_edit.text()
        if audio_pid:
            flags.append(f"{Pids.AUDIO.value}{int(audio_pid):04x}")
        teletext_pid = self.teletext_pid_edit.text()
        if teletext_pid:
            flags.append(f"{Pids.TELETEXT.value}{int(teletext_pid):04x}")
        pcr_pid = self.pcr_pid_edit.text()
        if pcr_pid:
            flags.append(f"{Pids.PCR.value}{int(pcr_pid):04x}")
        ac3_pid = self.ac3_pid_edit.text()
        if ac3_pid:
            flags.append(f"{Pids.AC3.value}{int(ac3_pid):04x}")
        pcm_pid = self.pcr_pid_edit.text()
        if pcm_pid:
            flags.append(f"{Pids.PCM_DELAY.value}{int(pcm_pid):04x}")
        extra_pids = self.extra_edit.text()
        if extra_pids:
            flags.append(extra_pids)
        # Flags.
        f_flags = Flag.KEEP.value if self.keep_flag_check_box.isChecked() else 0
        f_flags = f_flags + Flag.HIDE.value if self.hide_flag_check_box.isChecked() else f_flags
        f_flags = f_flags + Flag.PIDS.value if self.use_pids_flag_check_box.isChecked() else f_flags
        f_flags = f_flags + Flag.NEW.value if self.new_flag_check_box.isChecked() else f_flags
        if f_flags:
            flags.append(f"f:{f_flags:02d}")

        return ",".join(flags)

    def is_data_correct(self):
        return True

    def update_reference_entry(self):
        s_type = int(self.type_combo_box.model().index(self.type_combo_box.currentIndex(), 1).data())
        sid = int(self.sid_edit.text() or 0)
        ref = f"1:0:{s_type:X}:{sid:X}:{self._tid:X}:{self._nid:X}:{self._namespace:X}:0:0:0"
        self.ref_edit.setText(ref)

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("service_dialog", "E2Toolkit [Service]"))
        self.service_group_box.setTitle(_translate("service_dialog", "Service"))
        self.name_label.setText(_translate("service_dialog", "Name:"))
        self.package_label.setText(_translate("service_dialog", "Package:"))
        self.caids_label.setText(_translate("service_dialog", "CAID\'s:"))
        self.ref_label.setText(_translate("service_dialog", "Reference:"))
        self.type_label.setText(_translate("service_dialog", "Type:"))
        self.sid_label.setText(_translate("service_dialog", "SID:"))
        self.extra_label.setText(_translate("service_dialog", "Extra:"))
        self.pids_group_box.setTitle(_translate("service_dialog", "PID\'s"))
        self.video_label.setText(_translate("service_dialog", "Video"))
        self.ac3_label.setText(_translate("service_dialog", "AC3"))
        self.teletext_label.setText(_translate("service_dialog", "Teletext"))
        self.audio_label.setText(_translate("service_dialog", "Audio"))
        self.pcr_label.setText(_translate("service_dialog", "PCR"))
        self.ac3p_label.setText(_translate("service_dialog", "AC3+"))
        self.acc_label.setText(_translate("service_dialog", "ACC"))
        self.he_acc_label.setText(_translate("service_dialog", "HE-ACC"))
        self.flags_group_box.setTitle(_translate("service_dialog", "Flags"))
        self.keep_flag_check_box.setText(_translate("service_dialog", "Keep"))
        self.hide_flag_check_box.setText(_translate("service_dialog", "Hide"))
        self.use_pids_flag_check_box.setText(_translate("service_dialog", "Use PID\'s"))
        self.new_flag_check_box.setText(_translate("service_dialog", "New"))


class IptvServiceDialog(QtWidgets.QDialog):
    _ENIGMA2_REFERENCE = "{}:0:{}:{:X}:{:X}:{:X}:{:X}:0:0:0"

    class UrlValidator(QtGui.QRegExpValidator):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            rx = QtCore.QRegExp()
            rx.setPattern("https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]")
            self.setRegExp(rx)

    class IptvTypeModel(QtGui.QStandardItemModel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for t in ((self.tr("DVB/TS"), "1"), (self.tr("non-TS"), "4097"),
                      (self.tr("none-REC1"), "5001"), (self.tr("none-REC2"), "5002"),
                      (self.tr("eServiceUri"), "8193"), (self.tr("eServiceUri"), "8739")):
                self.appendRow((QtGui.QStandardItem(t[0]), QtGui.QStandardItem(t[1])))

    def __init__(self, service=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(f"{UI_PATH}iptv_service_dialog.ui", self)
        # Values validation.
        self.url_edit.setValidator(self.UrlValidator(self.url_edit))
        self.dvb_type_edit.setValidator(QtGui.QIntValidator(self.dvb_type_edit))
        self.sid_edit.setValidator(QtGui.QIntValidator(self.sid_edit))
        self.sid_edit.setValidator(QtGui.QIntValidator(self.sid_edit))
        self.tid_edit.setValidator(QtGui.QIntValidator(self.tid_edit))
        self.nid_edit.setValidator(QtGui.QIntValidator(self.nid_edit))
        self.namespace_edit.setValidator(QtGui.QIntValidator(self.namespace_edit))

        self.retranslate_ui()
        self.url_edit.textChanged.connect(self.check_input)
        QtCore.QMetaObject.connectSlotsByName(self)
        # Service type box
        self.type_combo_box.setModel(self.IptvTypeModel(self.type_combo_box))
        self.type_combo_box.currentTextChanged.connect(self.update_reference_entry)
        # Data init
        self._service = service
        self._desc = None
        self.init_service_data() if service else self.init_new_service_data()
        # Update reference
        self.sid_edit.textChanged.connect(self.update_reference_entry)
        self.tid_edit.textChanged.connect(self.update_reference_entry)
        self.nid_edit.textChanged.connect(self.update_reference_entry)
        self.namespace_edit.textChanged.connect(self.update_reference_entry)

    @property
    def service(self):
        return self._service

    def init_service_data(self):
        data, sep, desc = self._service.fav_id.partition("#DESCRIPTION")
        self._desc = desc.strip()

        data = data.split(":")
        if len(data) < 11:
            return

        self.name_edit.setText(self._service.name)
        self.dvb_type_edit.setText(data[2])
        self.sid_edit.setText(str(int(data[3], 16)))
        self.tid_edit.setText(str(int(data[4], 16)))
        self.nid_edit.setText(str(int(data[5], 16)))
        self.namespace_edit.setText(str(int(data[6], 16)))
        self.url_edit.setText(unquote(data[10].strip()))

        s_type = data[0].strip()
        stream_type = StreamType(s_type)
        if stream_type is StreamType.DVB_TS:
            self.type_combo_box.setCurrentIndex(0)
        elif stream_type is StreamType.NONE_TS:
            self.type_combo_box.setCurrentIndex(1)
        elif stream_type is StreamType.NONE_REC_1:
            self.type_combo_box.setCurrentIndex(2)
        elif stream_type is StreamType.NONE_REC_2:
            self.type_combo_box.setCurrentIndex(3)
        elif stream_type is StreamType.E_SERVICE_URI:
            self.type_combo_box.setCurrentIndex(4)
        elif stream_type is StreamType.E_SERVICE_HLS:
            self.type_combo_box.setCurrentIndex(5)
        else:
            log(f"Unknown stream type {s_type}")

    def init_new_service_data(self):
        self.dvb_type_edit.setText("1")
        self.sid_edit.setText("0")
        self.tid_edit.setText("0")
        self.nid_edit.setText("0")
        self.namespace_edit.setText("0")
        self.type_combo_box.setCurrentIndex(1)

    def accept(self):
        if not self.is_data_correct():
            return

        url = self.url_edit.text()
        name = self.name_edit.text().strip()
        stream_type = self.type_combo_box.model().index(self.type_combo_box.currentIndex(), 1).data()
        dvb_type = int(self.dvb_type_edit.text())
        params = (int(self.sid_edit.text()),
                  int(self.tid_edit.text()),
                  int(self.nid_edit.text()),
                  int(self.namespace_edit.text()))

        fav_id = get_fav_id(url, name, stream_type, params, dvb_type)
        p_id = "{}_0_{:X}_{}_{}_{}_{}_0_0_0.png".format(stream_type, dvb_type, *params)
        if not self._service:
            st = BqServiceType.IPTV.name
            aggr = [None] * 7
            self._service = Service(None, None, None, None, p_id, name, None, None, None, st, *aggr, url, fav_id, None)
        else:
            self._service = self._service._replace(picon_id=p_id, name=name, data_id=url, fav_id=fav_id)

        super().accept()

    def update_reference_entry(self):
        stream_type = self.type_combo_box.model().index(self.type_combo_box.currentIndex(), 1).data()
        self.ref_edit.setText(self._ENIGMA2_REFERENCE.format(stream_type,
                                                             self.dvb_type_edit.text(),
                                                             int(self.sid_edit.text() or 0),
                                                             int(self.tid_edit.text() or 0),
                                                             int(self.nid_edit.text() or 0),
                                                             int(self.namespace_edit.text() or 0)))

    def is_data_correct(self):
        url_validator = self.url_edit.validator()
        state = url_validator.validate(self.url_edit.text(), 0)[0]
        accept = state == url_validator.Acceptable
        if not accept:
            self.url_edit.setStyleSheet("QLineEdit {background-color: #ff4545;}")
            return accept

        if not self.name_edit.text():
            self.name_edit.setText(self.tr("Enter a name!"))
            return

        return True

    def check_input(self):
        sender = self.sender()
        state = sender.validator().validate(sender.text(), 0)[0]
        sender.setStyleSheet("QLineEdit {background-color: #ff4545;}" if state != QtGui.QValidator.Acceptable else "")

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("iptv_service_dialog", "E2Toolkit [IPTV service]"))
        self.url_group_box.setTitle(_translate("iptv_service_dialog", "Url"))
        self.service_group_box.setTitle(_translate("iptv_service_dialog", "Service"))
        self.name_label.setText(_translate("iptv_service_dialog", "Name:"))
        self.ref_label.setText(_translate("iptv_service_dialog", "Reference:"))
        self.type_label.setText(_translate("iptv_service_dialog", "Type:"))
        self.dvb_group_box.setTitle(_translate("iptv_service_dialog", "DVB/TS data"))
        self.sid_label.setText(_translate("iptv_service_dialog", "SID"))
        self.dvb_type_label.setText(_translate("iptv_service_dialog", "Type"))
        self.namespace_label.setText(_translate("iptv_service_dialog", "Namespace:"))


class BackupDialog(QtWidgets.QDialog):
    extracted = QtCore.pyqtSignal(str)

    def __init__(self, backup_path, data_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(f"{UI_PATH}backup_dialog.ui", self)

        self._data_path = data_path
        # Creating path when doesn't exist.
        QtCore.QDir().mkpath(backup_path)
        # Views.
        self.file_view = BackupFileView(backup_path, self.splitter)
        self.file_view.setMinimumSize(QtCore.QSize(48, 0))
        self.file_view.setObjectName("file_view")
        self.details_view = QtWidgets.QListView(self.splitter)
        self.details_view.setVisible(False)
        self.details_view.setModel(QtCore.QStringListModel(self.details_view))
        self.details_view.setObjectName("details_view")

        self.retranslate_ui()
        self.button_box.rejected.connect(self.reject)
        self.details_button.clicked["bool"].connect(self.details_view.setVisible)
        self.file_view.selectionModel().selectionChanged.connect(self.on_file_selection)
        self.restore_bouquets_button.clicked.connect(lambda: self.restore((".tv", ".radio")))
        self.restore_all_button.clicked.connect(lambda: self.restore(""))
        self.remove_button.clicked.connect(self.on_remove)
        QtCore.QMetaObject.connectSlotsByName(self)
        # Enabling buttons.
        self.update_buttons()

    def on_file_selection(self, selected, deselected):
        if not self.details_button.isChecked():
            return

        model = self.details_view.model()
        model.removeRows(0, model.rowCount())
        indexes = selected.indexes()
        if indexes:
            with zipfile.ZipFile(self.file_view.model().filePath(indexes[0])) as zip_file:
                model.setStringList(zip_file.namelist())

    def restore(self, extensions):
        if QtWidgets.QMessageBox.question(self, "", self.tr("Are you sure?")) != QtWidgets.QMessageBox.Yes:
            return

        rows = self.file_view.selectionModel().selectedRows(0)

        if not rows:
            QtWidgets.QMessageBox.critical(self, "", self.tr("No selected item!"))
        elif len(rows) > 1:
            QtWidgets.QMessageBox.critical(self, "", self.tr("Please, select only one item!"))
        else:
            with zipfile.ZipFile(self.file_view.model().filePath(rows[0])) as zf:
                [zf.extract(file, self._data_path) for file in zf.namelist() if file.endswith(extensions)]

            self.extracted.emit(self._data_path)
            QtWidgets.QMessageBox.information(self, "", self.tr("Done!"))

    def on_remove(self):
        if QtWidgets.QMessageBox.question(self, "", self.tr("Are you sure?")) != QtWidgets.QMessageBox.Yes:
            return

        for i in self.file_view.selectionModel().selectedRows(0):
            if QtCore.QFile(i.model().filePath(i)).remove():
                i.model().removeRow(i.row())

        self.update_buttons()

    def update_buttons(self):
        """ Updates buttons state. """
        enable = not QtCore.QDir(self.file_view.model().rootPath()).isEmpty()
        self.restore_bouquets_button.setEnabled(enable)
        self.restore_all_button.setEnabled(enable)
        self.remove_button.setEnabled(enable)

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("backup_dialog", "E2Toolkit [Backups]"))
        self.restore_bouquets_button.setToolTip(_translate("backup_dialog", "Restore bouquets"))
        self.restore_bouquets_button.setText(_translate("backup_dialog", "Restore bouquets"))
        self.restore_all_button.setToolTip(_translate("backup_dialog", "Restore all"))
        self.restore_all_button.setText(_translate("backup_dialog", "Restore all"))
        self.remove_button.setToolTip(_translate("backup_dialog", "Remove"))
        self.remove_button.setText(_translate("backup_dialog", "Remove"))
        self.details_button.setToolTip(_translate("backup_dialog", "Details"))
        self.details_button.setText(_translate("backup_dialog", "Details"))


class SatelliteDialog(QtWidgets.QDialog):

    def __init__(self, satellite, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(f"{UI_PATH}satellite_dialog.ui", self)

        self.retranslate_ui()

        self._satellite = satellite
        self.init_data()

    @property
    def satellite(self):
        return self._satellite

    def init_data(self):
        self.name_edit.setText(self._satellite.name)
        pos = int(self._satellite.position) / 10
        self.position_box.setValue(abs(pos))
        self.side_box.setCurrentText("W" if pos < 0 else "E")

    def accept(self):
        if not self.is_data_correct():
            return

        pos = f"{self.position_box.value() * (-10 if self.side_box.currentText() == 'W' else 10):0.1f}"
        self._satellite = self._satellite._replace(name=self.name_edit.text(), position=f"{int(float(pos)):d}")

        super().accept()

    def is_data_correct(self):
        return True

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("satellite_dialog", "E2Toolkit [Satellite]"))
        self.edit_box.setTitle(_translate("satellite_dialog", "Satellite"))
        self.name_label.setText(_translate("satellite_dialog", "Name:"))
        self.position_label.setText(_translate("satellite_dialog", "Position:"))


class TransponderDialog(QtWidgets.QDialog):

    def __init__(self, transponder, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(f"{UI_PATH}transponder_dialog.ui", self)
        # Boxes data.
        self.pol_combo_box.setModel(QtCore.QStringListModel(POLARIZATION.values()))
        self.fec_combo_box.setModel(QtCore.QStringListModel(sorted(set(FEC.values()))))
        self.system_combo_box.setModel(QtCore.QStringListModel(SYSTEM.values()))
        self.mod_combo_box.setModel(QtCore.QStringListModel(MODULATION.values()))
        self.pls_combo_box.setModel(QtCore.QStringListModel(tuple(PLS_MODE.values()) + ("None",)))
        # Value validation.
        self.freq_edit.setValidator(QtGui.QIntValidator(self.freq_edit))
        self.sr_edit.setValidator(QtGui.QIntValidator(self.sr_edit))
        self.pls_code_edit.setValidator(QtGui.QIntValidator(self.pls_code_edit))
        self.is_id_edit.setValidator(QtGui.QIntValidator(self.is_id_edit))

        self.retranslate_ui()

        self._tr = transponder
        self.init_data()

    @property
    def transponder(self):
        return self._tr

    def init_data(self):
        self.freq_edit.setText(self._tr.frequency)
        self.sr_edit.setText(self._tr.symbol_rate)
        self.pol_combo_box.setCurrentText(self._tr.polarization)
        self.fec_combo_box.setCurrentText(self._tr.fec_inner)
        self.system_combo_box.setCurrentText(self._tr.system)
        self.mod_combo_box.setCurrentText(self._tr.modulation)
        self.pls_combo_box.setCurrentText(str(self._tr.pls_mode))
        self.pls_code_edit.setText(self._tr.pls_code)
        self.is_id_edit.setText(self._tr.is_id)

    def accept(self):
        if not self.is_data_correct():
            return

        self._tr = self._tr._replace(frequency=self.freq_edit.text(),
                                     symbol_rate=self.sr_edit.text(),
                                     polarization=self.pol_combo_box.currentText(),
                                     fec_inner=self.fec_combo_box.currentText(),
                                     system=self.system_combo_box.currentText(),
                                     modulation=self.mod_combo_box.currentText(),
                                     pls_mode=get_key_by_value(PLS_MODE, self.pls_combo_box.currentText()),
                                     pls_code=self.pls_code_edit.text() or None,
                                     is_id=self.is_id_edit.text() or None)

        super().accept()

    def is_data_correct(self):
        return True

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("transponder_dialog", "E2Toolkit [Transponder]"))
        self.edit_box.setTitle(_translate("transponder_dialog", "Transponder"))
        self.freq_label.setText(_translate("transponder_dialog", "Freq:"))
        self.sr_label.setText(_translate("transponder_dialog", "SR:"))
        self.pol_label.setText(_translate("transponder_dialog", "Pol:"))
        self.fec_label.setText(_translate("transponder_dialog", "FEC:"))
        self.system_label.setText(_translate("transponder_dialog", "System:"))
        self.mod_label.setText(_translate("transponder_dialog", "Mod:"))
        self.pls_mode_label.setText(_translate("transponder_dialog", "PLS mode:"))
        self.pls_code_label.setText(_translate("transponder_dialog", "PLS code:"))
        self.is_id_label.setText(_translate("transponder_dialog", "Is ID:"))


class InputDialog(QtWidgets.QInputDialog):
    def __init__(self, title, label, width=320, height=-1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setInputMode(QtWidgets.QInputDialog.TextInput)
        self.setWindowTitle(self.tr(title))
        self.setLabelText(self.tr(label))
        self.resize(width, height)
