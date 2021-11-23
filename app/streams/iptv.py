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


""" Module for IPTV and streams support. """
import re
from enum import Enum
from urllib.parse import quote

from app.commons import log
from app.enigma.ecommons import BqServiceType, Service

ENIGMA2_FAV_ID_FORMAT = " {}:0:{}:{:X}:{:X}:{:X}:{:X}:0:0:0:{}:{}\n#DESCRIPTION: {}\n"
MARKER_FORMAT = " 1:64:{}:0:0:0:0:0:0:0::{}\n#DESCRIPTION {}\n"


class StreamType(Enum):
    DVB_TS = "1"
    NONE_TS = "4097"
    NONE_REC_1 = "5001"
    NONE_REC_2 = "5002"
    E_SERVICE_URI = "8193"
    E_SERVICE_HLS = "8739"
    NONE = "0"

    @classmethod
    def _missing_(cls, value):
        return cls.NONE


def import_m3u(path, stream_type=StreamType.NONE_TS.value, detect_encoding=True, params=None):
    with open(path, "rb") as file:
        data = file.read()
        encoding = "utf-8"

        if detect_encoding:
            try:
                import chardet
            except ModuleNotFoundError:
                pass
            else:
                enc = chardet.detect(data)
                encoding = enc.get("encoding", "utf-8")

        aggr = [None] * 7
        s_aggr = aggr[: -2]
        m_aggr = [None] * 8
        services = []
        groups = set()
        marker_counter = 1
        sid_counter = 1
        name = None
        picon = None
        p_id = "1_0_1_0_0_0_0_0_0_0.png"
        st = BqServiceType.IPTV.name
        params = params or [0, 0, 0, 0]

        for line in str(data, encoding=encoding, errors="ignore").splitlines():
            if line.startswith("#EXTINF"):
                line, sep, name = line.rpartition(",")

                data = re.split('"', line)
                size = len(data)
                if size < 3:
                    continue
                d = {data[i].lower().strip(" ="): data[i + 1] for i in range(0, len(data) - 1, 2)}
                picon = d.get("tvg-logo", None)

                grp_name = d.get("group-title", None)
                if grp_name not in groups:
                    groups.add(grp_name)
                    fav_id = MARKER_FORMAT.format(marker_counter, grp_name, grp_name)
                    marker_counter += 1
                    mr = Service(*s_aggr, grp_name, None, None, None, BqServiceType.MARKER.name, *m_aggr, fav_id, None)
                    services.append(mr)
            elif line.startswith("#EXTGRP"):
                grp_name = line.strip("#EXTGRP:").strip()
                if grp_name not in groups:
                    groups.add(grp_name)
                    fav_id = MARKER_FORMAT.format(marker_counter, grp_name, grp_name)
                    marker_counter += 1
                    mr = Service(*s_aggr, grp_name, None, None, None, BqServiceType.MARKER.name, *m_aggr, fav_id, None)
                    services.append(mr)
            elif not line.startswith("#"):
                url = line.strip()
                params[0] = sid_counter
                sid_counter += 1
                fav_id = get_fav_id(url, name, stream_type, params)
                if all((name, url, fav_id)):
                    srv = Service(None, None, None, None, p_id, name, None, None, None, st, *aggr, url, fav_id, None)
                    services.append(srv)
                else:
                    log("*.m3u* parse error ['{}']: name[{}], url[{}], fav id[{}]".format(path, name, url, fav_id))

    return services


def get_fav_id(url, service_name, stream_type=None, params=None, s_type=1):
    """ Returns fav id for IPTV service. """
    stream_type = stream_type or StreamType.NONE_TS.value
    params = params or (0, 0, 0, 0)
    return ENIGMA2_FAV_ID_FORMAT.format(stream_type, s_type, *params, quote(url), service_name, service_name, None)


if __name__ == "__main__":
    pass
