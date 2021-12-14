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


""" Common module for app constants and additional functions. """
# Application
APP_NAME = "E2Toolkit"
APP_VERSION = "1.0.0 Pre-Alpha"

# Just add your language to appear on the menu.
LOCALES = (("English", "en"), ("español", "es"), ("Deutsch", "de"),
           ("Nederlands", "nl"), ("polski", "pl"), ("português", "pt"),
           ("Türkçe", "tr"), ("беларуская", "be"), ("русский", "ru"))


# Logging
def log(message):
    print(message)


if __name__ == "__main__":
    pass
