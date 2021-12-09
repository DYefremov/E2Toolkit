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

""" Common UI module. """
from enum import IntEnum


# Icons
CODED_ICON = None
LOCKED_ICON = None
HIDE_ICON = None
IPTV_ICON = None


class BqGenType(IntEnum):
    """  Bouquet generation type. """
    SAT = 0
    EACH_SAT = 1
    PACKAGE = 2
    EACH_PACKAGE = 3
    TYPE = 4
    EACH_TYPE = 5


class Column(IntEnum):
    """ Column nums in the views. """
    # Services
    CAS_FLAGS = 0
    STANDARD = 1
    CODED = 2
    PICON = 3
    PICON_ID = 4
    NAME = 5
    LOCKED = 6
    HIDE = 7
    PACKAGE = 8
    TYPE = 9
    SSID = 10
    FREQ = 11
    RATE = 12
    POL = 13
    FEC = 14
    SYSTEM = 15
    POS = 16
    DATA_ID = 17
    FAV_ID = 18
    TRANSPONDER = 19
    # Bouquets
    BQ_NAME = 0
    BQ_LOCKED = 1
    BQ_HIDDEN = 2
    BQ_TYPE = 3
    # Picons
    PICON_INFO = 0
    PICON_PATH = 1
    PICON_IMG = 2
    # EPG
    EPG_TITLE = 0
    EPG_TIME = 1
    EPG_DESC = 2
    EPG_EVENT = 3
    # Timer
    TIMER_NAME = 0
    TIMER_DESC = 1
    TIMER_SRV = 2
    TIMER_TIME = 3
    TIMER_DATA = 4
    # Satellite
    SAT_NAME = 0
    SAT_POS = 1
    SAT_DATA = 2

    def __index__(self):
        """ Overridden to get the index in slices directly """
        return self.value
