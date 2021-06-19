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


""" Common module for app constants and additional functions. """
from PyQt5.QtCore import QLocale

# Application
APP_NAME = "E2Toolkit"
APP_VERSION = "1.0.0 Pre-Alpha"
# Translation
LANG_PATH = "ui/locale/"
LOCALES = (QLocale(QLocale.Spanish),
           QLocale(QLocale.German),
           QLocale(QLocale.Dutch),
           QLocale(QLocale.Polish),
           QLocale(QLocale.Portuguese),
           QLocale(QLocale.Turkish),
           QLocale(QLocale.Belarusian),
           QLocale(QLocale.Russian))
# Icons
CODED_ICON = None
LOCKED_ICON = None
HIDE_ICON = None


# Logging
def log(message):
    print(message)


if __name__ == "__main__":
    pass
