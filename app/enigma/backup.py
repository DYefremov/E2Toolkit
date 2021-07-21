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


""" Module for working with backups. """
import os
import shutil
from datetime import datetime


_XML_DATA = {"satellites.xml", "terrestrial.xml", "cables.xml"}


def backup_data(path, backup_path, move=True):
    """ Creating data backup from a folder at the specified path

        Returns full path to the compressed file.
    """
    backup_path = "{}{}/".format(backup_path, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Backup files in data dir(skipping dirs and *.xml)
    for file in filter(lambda f: f not in _XML_DATA and os.path.isfile(os.path.join(path, f)), os.listdir(path)):
        src, dst = os.path.join(path, file), backup_path + file
        shutil.move(src, dst) if move else shutil.copy(src, dst)
    # Compressing to zip and delete remaining files.
    zip_file = shutil.make_archive(backup_path, "zip", backup_path)
    shutil.rmtree(backup_path)

    return zip_file


def restore_data(src, dst):
    """ Unpacks backup data. """
    clear_data_path(dst)
    shutil.unpack_archive(src, dst)


def clear_data_path(path):
    """ Clearing data at the specified path excluding *.xml file. """
    for file in filter(lambda f: f not in _XML_DATA and os.path.isfile(os.path.join(path, f)), os.listdir(path)):
        os.remove(os.path.join(path, file))


if __name__ == "__main__":
    pass
