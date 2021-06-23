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


""" This module used for parsing blacklist file.

    Parent Lock/Unlock.
"""
from contextlib import suppress

__FILE_NAME = "blacklist"


def get_blacklist(path):
    with suppress(FileNotFoundError):
        with open(path + __FILE_NAME, "r") as file:
            # filter empty values and "\n"
            return {*list(filter(None, (x.strip() for x in file.readlines())))}
    return {}


def write_blacklist(path, channels):
    with open(path + __FILE_NAME, "w") as file:
        if channels:
            file.writelines("\n".join(channels))


if __name__ == "__main__":
    pass
