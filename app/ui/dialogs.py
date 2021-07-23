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


from urllib.parse import unquote

from PyQt5 import QtWidgets, QtCore, QtGui

from app.commons import log
from app.enigma.ecommons import Pids, Flag
from app.streams.iptv import StreamType
from app.ui.models import ServiceTypeModel


class TimerDialog(QtWidgets.QDialog):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("timer_dialog")
        self.resize(365, 490)
        self.setToolTip("")
        self.setModal(True)

        min_edit_width = 180

        self.dialog_grid_layout = QtWidgets.QGridLayout(self)
        self.dialog_grid_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.dialog_grid_layout.setObjectName("dialog_grid_layout")
        self.main_grid_layout = QtWidgets.QGridLayout()
        self.main_grid_layout.setObjectName("main_grid_layout")

        self.timer_edit_box = QtWidgets.QGroupBox(self)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.timer_edit_box.sizePolicy().hasHeightForWidth())
        self.timer_edit_box.setSizePolicy(size_policy)
        self.timer_edit_box.setObjectName("timer_edit_box")
        self.timer_edit_gruop_box = QtWidgets.QFormLayout(self.timer_edit_box)
        self.timer_edit_gruop_box.setContentsMargins(9, 9, 9, 9)
        self.timer_edit_gruop_box.setObjectName("timer_edit_gruop_box")
        # Enable
        self.timer_enable_widget = QtWidgets.QWidget(self.timer_edit_box)
        self.timer_enable_widget.setMinimumWidth(min_edit_width)
        self.timer_enable_widget.setObjectName("timer_enable_widget")
        self.timer_edit_enable_box = QtWidgets.QHBoxLayout(self.timer_enable_widget)
        self.timer_edit_enable_box.setContentsMargins(0, 0, 0, 0)
        self.timer_edit_enable_box.setObjectName("timer_edit_enable_box")
        spacer_item = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.timer_edit_enable_box.addItem(spacer_item)
        self.timer_enable_button = QtWidgets.QToolButton(self.timer_enable_widget)
        self.timer_enable_button.setMinimumSize(QtCore.QSize(85, 0))
        self.timer_enable_button.setCheckable(True)
        self.timer_enable_button.setObjectName("timer_enable_button")
        self.timer_edit_enable_box.addWidget(self.timer_enable_button)
        self.timer_edit_gruop_box.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.timer_enable_widget)
        # Name
        self.timer_name_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_name_label.setObjectName("timer_name_label")
        self.timer_edit_gruop_box.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.timer_name_label)
        self.timer_name_edit = QtWidgets.QLineEdit(self.timer_edit_box)
        self.timer_name_edit.setMinimumWidth(min_edit_width)
        self.timer_name_edit.setObjectName("timer_name_edit")
        self.timer_edit_gruop_box.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.timer_name_edit)
        # Description
        self.timer_description_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_description_label.setObjectName("timer_description_label")
        self.timer_edit_gruop_box.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.timer_description_label)
        self.timer_description_edit = QtWidgets.QLineEdit(self.timer_edit_box)
        self.timer_description_edit.setMinimumWidth(min_edit_width)
        self.timer_description_edit.setObjectName("timer_description_edit")
        self.timer_edit_gruop_box.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.timer_description_edit)
        # Service
        self.timer_service_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_service_label.setObjectName("timer_service_label")
        self.timer_edit_gruop_box.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.timer_service_label)
        self.timer_service_edit = QtWidgets.QLineEdit(self.timer_edit_box)
        self.timer_service_edit.setMinimumWidth(min_edit_width)
        self.timer_service_edit.setObjectName("timer_service_edit")
        self.timer_edit_gruop_box.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.timer_service_edit)
        # Reference
        self.timer_service_ref_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_service_ref_label.setObjectName("timer_service_ref_label")
        self.timer_edit_gruop_box.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.timer_service_ref_label)
        self.timer_ref_edit = QtWidgets.QLineEdit(self.timer_edit_box)
        self.timer_ref_edit.setMinimumWidth(min_edit_width)
        self.timer_ref_edit.setObjectName("timer_ref_edit")
        self.timer_edit_gruop_box.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.timer_ref_edit)
        # Event ID
        self.timer_event_id_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_event_id_label.setObjectName("timer_event_id_label")
        self.timer_edit_gruop_box.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.timer_event_id_label)
        self.timer_event_id_edit = QtWidgets.QLineEdit(self.timer_edit_box)
        self.timer_event_id_edit.setMinimumWidth(min_edit_width)
        self.timer_event_id_edit.setObjectName("timer_event_id_edit")
        self.timer_edit_gruop_box.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.timer_event_id_edit)
        # Begins
        self.timer_begins_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_begins_label.setObjectName("timer_begins_label")
        self.timer_edit_gruop_box.setWidget(6, QtWidgets.QFormLayout.LabelRole, self.timer_begins_label)
        self.timer_begins_edit = QtWidgets.QLineEdit(self.timer_edit_box)
        self.timer_begins_edit.setMinimumWidth(min_edit_width)
        self.timer_begins_edit.setReadOnly(True)
        self.timer_begins_edit.setObjectName("timer_begins_edit")
        self.timer_edit_gruop_box.setWidget(6, QtWidgets.QFormLayout.FieldRole, self.timer_begins_edit)
        # Ends
        self.timer_ends_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_ends_label.setObjectName("timer_ends_label")
        self.timer_edit_gruop_box.setWidget(7, QtWidgets.QFormLayout.LabelRole, self.timer_ends_label)
        self.timer_ends_edit = QtWidgets.QLineEdit(self.timer_edit_box)
        self.timer_ends_edit.setMinimumWidth(min_edit_width)
        self.timer_ends_edit.setReadOnly(True)
        self.timer_ends_edit.setObjectName("timer_ends_edit")
        self.timer_edit_gruop_box.setWidget(7, QtWidgets.QFormLayout.FieldRole, self.timer_ends_edit)
        # Repeated
        self.timer_repeated_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_repeated_label.setObjectName("timer_repeated_label")
        self.timer_edit_gruop_box.setWidget(8, QtWidgets.QFormLayout.LabelRole, self.timer_repeated_label)
        self.timer_repeated_grid = QtWidgets.QGridLayout()
        self.timer_repeated_grid.setContentsMargins(0, -1, 9, -1)
        self.timer_repeated_grid.setVerticalSpacing(0)
        self.timer_repeated_grid.setObjectName("timer_repeated_grid")
        self.timer_th_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_th_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_th_label.setObjectName("timer_th_label")
        self.timer_repeated_grid.addWidget(self.timer_th_label, 0, 3, 1, 1)
        self.timer_su_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_su_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_su_label.setObjectName("timer_su_label")
        self.timer_repeated_grid.addWidget(self.timer_su_label, 0, 6, 1, 1)
        self.timer_tu_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_tu_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_tu_label.setObjectName("timer_tu_label")
        self.timer_repeated_grid.addWidget(self.timer_tu_label, 0, 1, 1, 1)
        self.timer_sa_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_sa_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_sa_label.setObjectName("timer_sa_label")
        self.timer_repeated_grid.addWidget(self.timer_sa_label, 0, 5, 1, 1)
        self.timer_mo_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_mo_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_mo_label.setObjectName("timer_mo_label")
        self.timer_repeated_grid.addWidget(self.timer_mo_label, 0, 0, 1, 1)
        self.timer_we_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_we_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_we_label.setObjectName("timer_we_label")
        self.timer_repeated_grid.addWidget(self.timer_we_label, 0, 2, 1, 1)
        self.timer_fr_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_fr_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_fr_label.setObjectName("timer_fr_label")
        self.timer_repeated_grid.addWidget(self.timer_fr_label, 0, 4, 1, 1)
        self.timer_mo_check_box = QtWidgets.QCheckBox(self.timer_edit_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.timer_mo_check_box.sizePolicy().hasHeightForWidth())
        self.timer_mo_check_box.setSizePolicy(size_policy)
        self.timer_mo_check_box.setObjectName("timer_mo_check_box")
        self.timer_repeated_grid.addWidget(self.timer_mo_check_box, 1, 0, 1, 1)
        self.timer_tu_check_box = QtWidgets.QCheckBox(self.timer_edit_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.timer_tu_check_box.sizePolicy().hasHeightForWidth())
        self.timer_tu_check_box.setSizePolicy(size_policy)
        self.timer_tu_check_box.setObjectName("timer_tu_check_box")
        self.timer_repeated_grid.addWidget(self.timer_tu_check_box, 1, 1, 1, 1)
        self.timer_we_check_box = QtWidgets.QCheckBox(self.timer_edit_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.timer_we_check_box.sizePolicy().hasHeightForWidth())
        self.timer_we_check_box.setSizePolicy(size_policy)
        self.timer_we_check_box.setObjectName("timer_we_check_box")
        self.timer_repeated_grid.addWidget(self.timer_we_check_box, 1, 2, 1, 1)
        self.timer_th_check_box = QtWidgets.QCheckBox(self.timer_edit_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.timer_th_check_box.sizePolicy().hasHeightForWidth())
        self.timer_th_check_box.setSizePolicy(size_policy)
        self.timer_th_check_box.setObjectName("timer_th_check_box")
        self.timer_repeated_grid.addWidget(self.timer_th_check_box, 1, 3, 1, 1)
        self.timer_fr_check_box = QtWidgets.QCheckBox(self.timer_edit_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.timer_fr_check_box.sizePolicy().hasHeightForWidth())
        self.timer_fr_check_box.setSizePolicy(size_policy)
        self.timer_fr_check_box.setObjectName("timer_fr_check_box")
        self.timer_repeated_grid.addWidget(self.timer_fr_check_box, 1, 4, 1, 1)
        self.timer_sa_check_box = QtWidgets.QCheckBox(self.timer_edit_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.timer_sa_check_box.sizePolicy().hasHeightForWidth())
        self.timer_sa_check_box.setSizePolicy(size_policy)
        self.timer_sa_check_box.setObjectName("timer_sa_check_box")
        self.timer_repeated_grid.addWidget(self.timer_sa_check_box, 1, 5, 1, 1)
        self.timer_su_check_box = QtWidgets.QCheckBox(self.timer_edit_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.timer_su_check_box.sizePolicy().hasHeightForWidth())
        self.timer_su_check_box.setSizePolicy(size_policy)
        self.timer_su_check_box.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.timer_su_check_box.setObjectName("timer_su_check_box")
        self.timer_repeated_grid.addWidget(self.timer_su_check_box, 1, 6, 1, 1)
        self.timer_edit_gruop_box.setLayout(8, QtWidgets.QFormLayout.FieldRole, self.timer_repeated_grid)
        # Action
        self.timer_action_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_action_label.setObjectName("timer_action_label")
        self.timer_edit_gruop_box.setWidget(9, QtWidgets.QFormLayout.LabelRole, self.timer_action_label)
        self.timer_action_combo_box = QtWidgets.QComboBox(self.timer_edit_box)
        self.timer_action_combo_box.setMinimumWidth(min_edit_width)
        self.timer_action_combo_box.setObjectName("timer_action_combo_box")
        self.timer_action_combo_box.setModel(self.TimerActionModel(self.timer_action_combo_box))
        self.timer_edit_gruop_box.setWidget(9, QtWidgets.QFormLayout.FieldRole, self.timer_action_combo_box)
        # After event
        self.timer_after_event_label = QtWidgets.QLabel(self.timer_edit_box)
        self.timer_after_event_label.setObjectName("timer_after_event_label")
        self.timer_edit_gruop_box.setWidget(10, QtWidgets.QFormLayout.LabelRole, self.timer_after_event_label)
        self.timer_after_event_combo_box = QtWidgets.QComboBox(self.timer_edit_box)
        self.timer_after_event_combo_box.setMinimumWidth(min_edit_width)
        self.timer_after_event_combo_box.setObjectName("timer_after_event_combo_box")
        self.timer_after_event_combo_box.setModel(self.TimerAfterEventModel(self.timer_after_event_combo_box))
        self.timer_edit_gruop_box.setWidget(10, QtWidgets.QFormLayout.FieldRole, self.timer_after_event_combo_box)
        self.timer_location_label = QtWidgets.QLabel(self.timer_edit_box)
        # Location
        self.timer_location_label.setObjectName("timer_location_label")
        self.timer_edit_gruop_box.setWidget(11, QtWidgets.QFormLayout.LabelRole, self.timer_location_label)
        self.timer_location_combo_box = QtWidgets.QComboBox(self.timer_edit_box)
        self.timer_location_combo_box.setMinimumWidth(min_edit_width)
        self.timer_location_combo_box.setObjectName("timer_location_combo_box")
        self.timer_edit_gruop_box.setWidget(11, QtWidgets.QFormLayout.FieldRole, self.timer_location_combo_box)
        self.main_grid_layout.addWidget(self.timer_edit_box, 0, 0, 1, 1)
        # Button box
        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Save)
        self.button_box.setObjectName("button_box")
        self.main_grid_layout.addWidget(self.button_box, 1, 0, 1, 1)
        self.dialog_grid_layout.addLayout(self.main_grid_layout, 0, 0, 1, 1)

        self.retranslate_ui()
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("timer_dialog", "E2Toolkit [Timer]"))
        self.timer_enable_button.setText(_translate("timer_dialog", "Enabled"))
        self.timer_name_label.setText(_translate("timer_dialog", "Name:"))
        self.timer_description_label.setText(_translate("timer_dialog", "Description:"))
        self.timer_service_label.setText(_translate("timer_dialog", "Service:"))
        self.timer_service_ref_label.setText(_translate("timer_dialog", "Service reference:"))
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
        self.setObjectName("service_dialog")
        self.resize(330, 470)
        self.setModal(True)

        min_edit_width = 220

        self.dialog_layout = QtWidgets.QGridLayout(self)
        self.dialog_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.dialog_layout.setObjectName("dialog_layout")
        self.main_vertical_layout = QtWidgets.QVBoxLayout()
        self.main_vertical_layout.setObjectName("main_vertical_layout")
        self.service_group_box = QtWidgets.QGroupBox(self)
        self.service_group_box.setObjectName("service_group_box")
        self.service_group_box_layout = QtWidgets.QFormLayout(self.service_group_box)
        self.service_group_box_layout.setContentsMargins(6, 6, 6, 6)
        self.service_group_box_layout.setObjectName("service_group_box_layout")
        # Labels
        self.name_label = QtWidgets.QLabel(self.service_group_box)
        self.name_label.setObjectName("name_label")
        self.service_group_box_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.name_label)
        self.package_label = QtWidgets.QLabel(self.service_group_box)
        self.package_label.setObjectName("package_label")
        self.service_group_box_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.package_label)
        self.caids_label = QtWidgets.QLabel(self.service_group_box)
        self.caids_label.setObjectName("caids_label")
        self.service_group_box_layout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.caids_label)
        self.ref_label = QtWidgets.QLabel(self.service_group_box)
        self.ref_label.setObjectName("ref_label")
        self.service_group_box_layout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.ref_label)
        # Name
        self.name_edit = QtWidgets.QLineEdit(self.service_group_box)
        self.name_edit.setMinimumWidth(min_edit_width)
        self.name_edit.setObjectName("name_edit")
        self.service_group_box_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.name_edit)
        # Package
        self.package_edit = QtWidgets.QLineEdit(self.service_group_box)
        self.package_edit.setMinimumWidth(min_edit_width)
        self.package_edit.setObjectName("package_edit")
        self.service_group_box_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.package_edit)
        # CaID
        self.caids_edit = QtWidgets.QLineEdit(self.service_group_box)
        self.caids_edit.setMinimumWidth(min_edit_width)
        self.caids_edit.setObjectName("caids_edit")
        self.service_group_box_layout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.caids_edit)
        # Reference
        self.ref_edit = QtWidgets.QLineEdit(self.service_group_box)
        self.ref_edit.setMinimumWidth(min_edit_width)
        self.ref_edit.setObjectName("ref_edit")
        self.service_group_box_layout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.ref_edit)
        # SSID
        self.sid_type_layout = QtWidgets.QGridLayout()
        self.sid_type_layout.setObjectName("gridLayout_2")
        self.type_label = QtWidgets.QLabel(self.service_group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.type_label.sizePolicy().hasHeightForWidth())
        self.type_label.setSizePolicy(size_policy)
        self.type_label.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.type_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.type_label.setObjectName("type_label")
        self.sid_type_layout.addWidget(self.type_label, 0, 2, 1, 1)
        self.ssid_edit = QtWidgets.QLineEdit(self.service_group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.ssid_edit.sizePolicy().hasHeightForWidth())
        self.ssid_edit.setSizePolicy(size_policy)
        self.ssid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.ssid_edit.setObjectName("ssid_edit")
        self.sid_type_layout.addWidget(self.ssid_edit, 0, 1, 1, 1)
        self.type_combo_box = QtWidgets.QComboBox(self.service_group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Ignored)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.type_combo_box.sizePolicy().hasHeightForWidth())
        self.type_combo_box.setSizePolicy(size_policy)
        self.type_combo_box.setMinimumSize(QtCore.QSize(100, 0))
        self.type_combo_box.setObjectName("type_combo_box")
        self.sid_type_layout.addWidget(self.type_combo_box, 0, 3, 1, 1)
        self.service_group_box_layout.setLayout(4, QtWidgets.QFormLayout.FieldRole, self.sid_type_layout)
        self.ssid_label = QtWidgets.QLabel(self.service_group_box)
        self.ssid_label.setObjectName("ssid_label")
        self.service_group_box_layout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.ssid_label)
        # Extra
        self.extra_label = QtWidgets.QLabel(self.service_group_box)
        self.extra_label.setObjectName("extra_label")
        self.service_group_box_layout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.extra_label)
        self.extra_edit = QtWidgets.QLineEdit(self.service_group_box)
        self.extra_edit.setMinimumWidth(min_edit_width)
        self.extra_edit.setObjectName("extra_edit")
        self.service_group_box_layout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.extra_edit)
        self.main_vertical_layout.addWidget(self.service_group_box)
        # Pids
        self.pids_group_box = QtWidgets.QGroupBox(self)
        self.pids_group_box.setObjectName("pids_group_box")
        self.pids_group_box_layout = QtWidgets.QGridLayout(self.pids_group_box)
        self.pids_group_box_layout.setContentsMargins(6, 6, 6, 6)
        self.pids_group_box_layout.setObjectName("pids_group_box_layout")
        self.video_label = QtWidgets.QLabel(self.pids_group_box)
        self.video_label.setAlignment(QtCore.Qt.AlignCenter)
        self.video_label.setObjectName("video_label")
        self.pids_group_box_layout.addWidget(self.video_label, 0, 0, 1, 1)
        self.ac3_label = QtWidgets.QLabel(self.pids_group_box)
        self.ac3_label.setAlignment(QtCore.Qt.AlignCenter)
        self.ac3_label.setObjectName("ac3_label")
        self.pids_group_box_layout.addWidget(self.ac3_label, 3, 0, 1, 1)
        self.teletext_label = QtWidgets.QLabel(self.pids_group_box)
        self.teletext_label.setAlignment(QtCore.Qt.AlignCenter)
        self.teletext_label.setObjectName("teletext_label")
        self.pids_group_box_layout.addWidget(self.teletext_label, 0, 2, 1, 1)
        self.video_pid_edit = QtWidgets.QLineEdit(self.pids_group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.video_pid_edit.sizePolicy().hasHeightForWidth())
        self.video_pid_edit.setSizePolicy(size_policy)
        self.video_pid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.video_pid_edit.setObjectName("video_pid_edit")
        self.pids_group_box_layout.addWidget(self.video_pid_edit, 2, 0, 1, 1)
        self.audio_pid_edit = QtWidgets.QLineEdit(self.pids_group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.audio_pid_edit.sizePolicy().hasHeightForWidth())
        self.audio_pid_edit.setSizePolicy(size_policy)
        self.audio_pid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.audio_pid_edit.setObjectName("audio_pid_edit")
        self.pids_group_box_layout.addWidget(self.audio_pid_edit, 2, 1, 1, 1)
        self.teletext_pid_edit = QtWidgets.QLineEdit(self.pids_group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.teletext_pid_edit.sizePolicy().hasHeightForWidth())
        self.teletext_pid_edit.setSizePolicy(size_policy)
        self.teletext_pid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.teletext_pid_edit.setObjectName("teletext_pid_edit")
        self.pids_group_box_layout.addWidget(self.teletext_pid_edit, 2, 2, 1, 1)
        self.audio_label = QtWidgets.QLabel(self.pids_group_box)
        self.audio_label.setAlignment(QtCore.Qt.AlignCenter)
        self.audio_label.setObjectName("audio_label")
        self.pids_group_box_layout.addWidget(self.audio_label, 0, 1, 1, 1)
        self.pcr_label = QtWidgets.QLabel(self.pids_group_box)
        self.pcr_label.setAlignment(QtCore.Qt.AlignCenter)
        self.pcr_label.setObjectName("pcr_label")
        self.pids_group_box_layout.addWidget(self.pcr_label, 0, 3, 1, 1)
        self.pcr_pid_edit = QtWidgets.QLineEdit(self.pids_group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.pcr_pid_edit.sizePolicy().hasHeightForWidth())
        self.pcr_pid_edit.setSizePolicy(size_policy)
        self.pcr_pid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.pcr_pid_edit.setObjectName("pcr_pid_edit")
        self.pids_group_box_layout.addWidget(self.pcr_pid_edit, 2, 3, 1, 1)
        self.ac3p_label = QtWidgets.QLabel(self.pids_group_box)
        self.ac3p_label.setAlignment(QtCore.Qt.AlignCenter)
        self.ac3p_label.setObjectName("ac3p_label")
        self.pids_group_box_layout.addWidget(self.ac3p_label, 3, 1, 1, 1)
        self.acc_label = QtWidgets.QLabel(self.pids_group_box)
        self.acc_label.setAlignment(QtCore.Qt.AlignCenter)
        self.acc_label.setObjectName("acc_label")
        self.pids_group_box_layout.addWidget(self.acc_label, 3, 2, 1, 1)
        self.he_acc_label = QtWidgets.QLabel(self.pids_group_box)
        self.he_acc_label.setAlignment(QtCore.Qt.AlignCenter)
        self.he_acc_label.setObjectName("he_acc_label")
        self.pids_group_box_layout.addWidget(self.he_acc_label, 3, 3, 1, 1)
        self.ac3_pid_edit = QtWidgets.QLineEdit(self.pids_group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.ac3_pid_edit.sizePolicy().hasHeightForWidth())
        self.ac3_pid_edit.setSizePolicy(size_policy)
        self.ac3_pid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.ac3_pid_edit.setObjectName("ac3_pid_edit")
        self.pids_group_box_layout.addWidget(self.ac3_pid_edit, 4, 0, 1, 1)
        self.ac3p_pid_edit = QtWidgets.QLineEdit(self.pids_group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.ac3p_pid_edit.sizePolicy().hasHeightForWidth())
        self.ac3p_pid_edit.setSizePolicy(size_policy)
        self.ac3p_pid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.ac3p_pid_edit.setObjectName("ac3p_pid_edit")
        self.pids_group_box_layout.addWidget(self.ac3p_pid_edit, 4, 1, 1, 1)
        self.acc_pid_edit = QtWidgets.QLineEdit(self.pids_group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.acc_pid_edit.sizePolicy().hasHeightForWidth())
        self.acc_pid_edit.setSizePolicy(size_policy)
        self.acc_pid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.acc_pid_edit.setObjectName("acc_pid_edit")
        self.pids_group_box_layout.addWidget(self.acc_pid_edit, 4, 2, 1, 1)
        self.he_acc_pid_edit = QtWidgets.QLineEdit(self.pids_group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.he_acc_pid_edit.sizePolicy().hasHeightForWidth())
        self.he_acc_pid_edit.setSizePolicy(size_policy)
        self.he_acc_pid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.he_acc_pid_edit.setObjectName("he_acc_pid_edit")
        self.pids_group_box_layout.addWidget(self.he_acc_pid_edit, 4, 3, 1, 1)
        self.main_vertical_layout.addWidget(self.pids_group_box)
        # Flags
        self.flags_group_box = QtWidgets.QGroupBox(self)
        self.flags_group_box.setObjectName("flags_group_box")
        self.flags_group_box_layout = QtWidgets.QHBoxLayout(self.flags_group_box)
        self.flags_group_box_layout.setContentsMargins(6, 6, 6, 6)
        self.flags_group_box_layout.setObjectName("flags_group_box_layout")
        self.keep_flag_check_box = QtWidgets.QCheckBox(self.flags_group_box)
        self.keep_flag_check_box.setObjectName("keep_flag_check_box")
        self.flags_group_box_layout.addWidget(self.keep_flag_check_box)
        self.hide_flag_check_box = QtWidgets.QCheckBox(self.flags_group_box)
        self.hide_flag_check_box.setObjectName("hide_flag_check_box")
        self.flags_group_box_layout.addWidget(self.hide_flag_check_box)
        self.use_pids_flag_check_box = QtWidgets.QCheckBox(self.flags_group_box)
        self.use_pids_flag_check_box.setObjectName("use_pids_flag_check_box")
        self.flags_group_box_layout.addWidget(self.use_pids_flag_check_box)
        self.new_flag_check_box = QtWidgets.QCheckBox(self.flags_group_box)
        self.new_flag_check_box.setObjectName("new_flag_check_box")
        self.flags_group_box_layout.addWidget(self.new_flag_check_box)
        self.main_vertical_layout.addWidget(self.flags_group_box)
        self.dialog_layout.addLayout(self.main_vertical_layout, 0, 0, 1, 1)
        # Button box
        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Save)
        self.button_box.setObjectName("button_box")
        self.dialog_layout.addWidget(self.button_box, 1, 0, 1, 1)
        # Types.
        self.type_combo_box.setModel(ServiceTypeModel(self.type_combo_box))
        self.type_combo_box.currentTextChanged.connect(self.update_reference_entry)
        self.ssid_edit.textChanged.connect(self.update_reference_entry)
        # Value validation.
        self.ssid_edit.setValidator(QtGui.QIntValidator(self.ssid_edit))
        self.video_pid_edit.setValidator(QtGui.QIntValidator(self.video_pid_edit))
        self.audio_pid_edit.setValidator(QtGui.QIntValidator(self.audio_pid_edit))
        self.teletext_pid_edit.setValidator(QtGui.QIntValidator(self.teletext_pid_edit))
        self.pcr_pid_edit.setValidator(QtGui.QIntValidator(self.pcr_pid_edit))
        self.ac3_pid_edit.setValidator(QtGui.QIntValidator(self.ac3_pid_edit))
        self.ac3p_pid_edit.setValidator(QtGui.QIntValidator(self.ac3p_pid_edit))
        self.acc_pid_edit.setValidator(QtGui.QIntValidator(self.acc_pid_edit))
        self.he_acc_pid_edit.setValidator(QtGui.QIntValidator(self.he_acc_pid_edit))

        self.retranslate_ui()
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        QtCore.QMetaObject.connectSlotsByName(self)
        # Data init
        self._service = service
        self._tid = 0
        self._nid = 0
        self._namespace = 0
        self.init_service_data()

    def init_service_data(self):
        """ Service data initialisation. """
        self.name_edit.setText(self._service.name)
        self.package_edit.setText(self._service.package)
        self.ssid_edit.setText(str(int(self._service.ssid, 16)))
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

    def init_flags(self, flags):
        f_flags = list(filter(lambda x: x.startswith("f:"), flags))
        if f_flags:
            value = int(f_flags[0][2:])
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

    def update_reference_entry(self):
        s_type = int(self.type_combo_box.model().index(self.type_combo_box.currentIndex(), 1).data())
        ssid = int(self.ssid_edit.text() or 0)
        ref = "1:0:{:X}:{:X}:{:X}:{:X}:{:X}:0:0:0".format(s_type, ssid, self._tid, self._nid, self._namespace)
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
        self.ssid_label.setText(_translate("service_dialog", "SSID:"))
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

    class IptvTypeModel(QtGui.QStandardItemModel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for t in ((self.tr("DVB/TS"), "1"), (self.tr("non-TS"), "4097"),
                      (self.tr("none-REC1"), "5001"), (self.tr("none-REC2"), "5002"),
                      (self.tr("eServiceUri"), "8193"), (self.tr("eServiceUri"), "8739")):
                self.appendRow((QtGui.QStandardItem(t[0]), QtGui.QStandardItem(t[1])))

    def __init__(self, service, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("iptv_service_dialog")
        self.resize(300, 380)
        self.setModal(True)

        min_edit_width = 180

        self.main_dialog_layout = QtWidgets.QGridLayout(self)
        self.main_dialog_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.main_dialog_layout.setObjectName("main_dialog_layout")
        self.dialog_layout = QtWidgets.QVBoxLayout()
        self.dialog_layout.setObjectName("dialog_layout")
        # Url
        self.url_group_box = QtWidgets.QGroupBox(self)
        self.url_group_box.setObjectName("url_group_box")
        self.url_layout = QtWidgets.QHBoxLayout(self.url_group_box)
        self.url_layout.setContentsMargins(6, 6, 6, 6)
        self.url_layout.setObjectName("url_layout")
        self.url_edit = QtWidgets.QLineEdit(self.url_group_box)
        self.url_edit.setObjectName("url_edit")
        self.url_layout.addWidget(self.url_edit)
        self.dialog_layout.addWidget(self.url_group_box)
        # Service
        self.service_group_box = QtWidgets.QGroupBox(self)
        self.service_group_box.setObjectName("service_group_box")
        self.service_layout = QtWidgets.QFormLayout(self.service_group_box)
        self.service_layout.setContentsMargins(6, 6, 6, 6)
        self.service_layout.setObjectName("service_layout")
        self.name_label = QtWidgets.QLabel(self.service_group_box)
        self.name_label.setObjectName("name_label")
        self.service_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.name_label)
        self.name_edit = QtWidgets.QLineEdit(self.service_group_box)
        self.name_edit.setMinimumWidth(min_edit_width)
        self.name_edit.setObjectName("name_edit")
        self.service_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.name_edit)
        self.ref_label = QtWidgets.QLabel(self.service_group_box)
        self.ref_label.setObjectName("ref_label")
        self.service_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.ref_label)
        self.ref_edit = QtWidgets.QLineEdit(self.service_group_box)
        self.ref_edit.setMinimumWidth(min_edit_width)
        self.ref_edit.setObjectName("ref_edit")
        self.service_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.ref_edit)
        self.type_label = QtWidgets.QLabel(self.service_group_box)
        self.type_label.setObjectName("type_label")
        self.service_layout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.type_label)
        self.type_combo_box = QtWidgets.QComboBox(self.service_group_box)
        self.type_combo_box.setMinimumWidth(min_edit_width)
        self.type_combo_box.setObjectName("type_combo_box")
        self.service_layout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.type_combo_box)
        self.dialog_layout.addWidget(self.service_group_box)
        # DVB/TS data
        self.dvb_group_box = QtWidgets.QGroupBox(self)
        self.dvb_group_box.setObjectName("dvb_group_box")
        self.dvb_data_box_layout = QtWidgets.QVBoxLayout(self.dvb_group_box)
        self.dvb_data_box_layout.setContentsMargins(6, 6, 6, 6)
        self.dvb_data_box_layout.setObjectName("dvb_data_box_layout")
        self.dvb_data_layout = QtWidgets.QGridLayout()
        self.dvb_data_layout.setObjectName("dvb_data_layout")
        self.nid_label = QtWidgets.QLabel(self.dvb_group_box)
        self.nid_label.setText("NID")
        self.nid_label.setAlignment(QtCore.Qt.AlignCenter)
        self.nid_label.setObjectName("nid_label")
        self.dvb_data_layout.addWidget(self.nid_label, 0, 3, 1, 1)
        self.ssid_label = QtWidgets.QLabel(self.dvb_group_box)
        self.ssid_label.setAlignment(QtCore.Qt.AlignCenter)
        self.ssid_label.setObjectName("ssid_label")
        self.dvb_data_layout.addWidget(self.ssid_label, 0, 1, 1, 1)
        self.tid_label = QtWidgets.QLabel(self.dvb_group_box)
        self.tid_label.setText("TID")
        self.tid_label.setAlignment(QtCore.Qt.AlignCenter)
        self.tid_label.setObjectName("tid_label")
        self.dvb_data_layout.addWidget(self.tid_label, 0, 2, 1, 1)
        self.dvb_type_label = QtWidgets.QLabel(self.dvb_group_box)
        self.dvb_type_label.setAlignment(QtCore.Qt.AlignCenter)
        self.dvb_type_label.setObjectName("dvb_type_label")
        self.dvb_data_layout.addWidget(self.dvb_type_label, 0, 0, 1, 1)
        self.dvb_type_edit = QtWidgets.QLineEdit(self.dvb_group_box)
        self.dvb_type_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.dvb_type_edit.setObjectName("dvb_type_edit")
        self.dvb_data_layout.addWidget(self.dvb_type_edit, 1, 0, 1, 1)
        self.ssid_edit = QtWidgets.QLineEdit(self.dvb_group_box)
        self.ssid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.ssid_edit.setObjectName("ssid_edit")
        self.dvb_data_layout.addWidget(self.ssid_edit, 1, 1, 1, 1)
        self.tid_edit = QtWidgets.QLineEdit(self.dvb_group_box)
        self.tid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.tid_edit.setObjectName("tid_edit")
        self.dvb_data_layout.addWidget(self.tid_edit, 1, 2, 1, 1)
        self.nid_edit = QtWidgets.QLineEdit(self.dvb_group_box)
        self.nid_edit.setMaximumSize(QtCore.QSize(70, 16777215))
        self.nid_edit.setObjectName("nid_edit")
        self.dvb_data_layout.addWidget(self.nid_edit, 1, 3, 1, 1)
        self.dvb_data_box_layout.addLayout(self.dvb_data_layout)
        self.namespace_layout = QtWidgets.QHBoxLayout()
        self.namespace_layout.setObjectName("namespace_layout")
        self.namespace_label = QtWidgets.QLabel(self.dvb_group_box)
        self.namespace_label.setObjectName("namespace_label")
        self.namespace_layout.addWidget(self.namespace_label)
        self.namespace_edit = QtWidgets.QLineEdit(self.dvb_group_box)
        self.namespace_edit.setMinimumWidth(min_edit_width)
        self.namespace_edit.setObjectName("namespace_edit")
        self.namespace_layout.addWidget(self.namespace_edit)
        self.dvb_data_box_layout.addLayout(self.namespace_layout)
        self.dialog_layout.addWidget(self.dvb_group_box)
        self.main_dialog_layout.addLayout(self.dialog_layout, 0, 0, 1, 1)
        # Button box
        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Save)
        self.button_box.setObjectName("button_box")
        self.main_dialog_layout.addWidget(self.button_box, 1, 0, 1, 1)

        self.retranslate_ui()
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)
        QtCore.QMetaObject.connectSlotsByName(self)
        # Service type box
        self.type_combo_box.setModel(self.IptvTypeModel(self.type_combo_box))
        self.type_combo_box.currentTextChanged.connect(self.update_reference_entry)
        # Data init
        self._service = service
        self._desc = service.name
        self.init_service_data()

    def init_service_data(self):
        data, sep, desc = self._service.fav_id.partition("#DESCRIPTION")
        self._desc = desc.strip()

        data = data.split(":")
        if len(data) < 11:
            return

        self.dvb_type_edit.setText(data[2])
        self.ssid_edit.setText(str(int(data[3], 16)))
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
            log("Unknown stream type {}".format(s_type))

    def update_reference_entry(self):
        stream_type = self.type_combo_box.model().index(self.type_combo_box.currentIndex(), 1).data()
        self.ref_edit.setText(self._ENIGMA2_REFERENCE.format(stream_type,
                                                             self.dvb_type_edit.text(),
                                                             int(self.ssid_edit.text()),
                                                             int(self.tid_edit.text()),
                                                             int(self.nid_edit.text()),
                                                             int(self.namespace_edit.text())))

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("iptv_service_dialog", "E2Toolkit [IPTV service]"))
        self.url_group_box.setTitle(_translate("iptv_service_dialog", "Url"))
        self.service_group_box.setTitle(_translate("iptv_service_dialog", "Service"))
        self.name_label.setText(_translate("iptv_service_dialog", "Name:"))
        self.ref_label.setText(_translate("iptv_service_dialog", "Reference:"))
        self.type_label.setText(_translate("iptv_service_dialog", "Type:"))
        self.dvb_group_box.setTitle(_translate("iptv_service_dialog", "DVB/TS data"))
        self.ssid_label.setText(_translate("iptv_service_dialog", "SSID"))
        self.dvb_type_label.setText(_translate("iptv_service_dialog", "Type"))
        self.namespace_label.setText(_translate("iptv_service_dialog", "Namespace:"))
