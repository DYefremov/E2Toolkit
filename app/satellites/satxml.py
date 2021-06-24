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

""" Module for parsing the satellites.xml file.

    For more info see __COMMENT
"""
from xml.dom.minidom import parse, Document

from app.commons import log
from app.enigma.ecommons import POLARIZATION, FEC, SYSTEM, MODULATION, Transponder, Satellite

__COMMENT = ("This file was created in E2Toolkit.\n\n"
             "usable flags are\n"
             "	1: Network Scan\n"
             "	2: use BAT\n"
             "	4: use ONIT\n"
             "	8: skip NITs of known networks\n"
             "	and combinations of this.\n\n"

             "transponder parameters:\n"
             "polarization: 0 - Horizontal, 1 - Vertical, 2 - Left Circular, 3 - Right Circular\n"
             "fec_inner: 0 - Auto, 1 - 1/2, 2 - 2/3, 3 - 3/4, 4 - 5/6, 5 - 7/8, 6 -  8/9, 7 - 3/5,\n"
             "8 - 4/5, 9 - 9/10, 15 - None\n"
             "modulation: 0 - Auto, 1 - QPSK, 2 - 8PSK, 4 - 16APSK, 5 - 32APSK\n"
             "rolloff: 0 - 0.35, 1 - 0.25, 2 - 0.20, 3 - Auto\n"
             "pilot: 0 - Off, 1 - On, 2 - Auto\n"
             "inversion: 0 = Off, 1 = On, 2 = Auto (default)\n"
             "system: 0 = DVB-S, 1 = DVB-S2\n"
             "is_id: 0 - 255\n"
             "pls_mode: 0 - Root, 1 - Gold, 2 - Combo\n"
             "pls_code: 0 - 262142\n\n")


def get_satellites(path):
    """ Returns a list of satellites extracted from *.xml. """
    dom = parse(path)
    satellites = []

    for elem in dom.getElementsByTagName("sat"):
        if elem.hasAttributes():
            satellites.append(parse_sat(elem))

    return satellites


def write_satellites(satellites, data_path):
    """ Creation satellites.xml file. """
    doc = Document()
    comment = doc.createComment(__COMMENT)
    doc.appendChild(comment)
    root = doc.createElement("satellites")
    doc.appendChild(root)

    for sat in satellites:
        #    Create Element
        sat_child = doc.createElement("sat")
        sat_child.setAttribute("name", sat.name)
        sat_child.setAttribute("flags", sat.flags)
        sat_child.setAttribute("position", sat.position)

        for tr in sat.transponders:
            transponder_child = doc.createElement("transponder")
            transponder_child.setAttribute("frequency", tr.frequency)
            transponder_child.setAttribute("symbol_rate", tr.symbol_rate)
            transponder_child.setAttribute("polarization", get_key_by_value(POLARIZATION, tr.polarization))
            transponder_child.setAttribute("fec_inner", get_key_by_value(FEC, tr.fec_inner) or "0")
            transponder_child.setAttribute("system", get_key_by_value(SYSTEM, tr.system) or "0")
            transponder_child.setAttribute("modulation", get_key_by_value(MODULATION, tr.modulation) or "0")
            if tr.pls_mode:
                transponder_child.setAttribute("pls_mode", tr.pls_mode)
            if tr.pls_code:
                transponder_child.setAttribute("pls_code", tr.pls_code)
            if tr.is_id:
                transponder_child.setAttribute("is_id", tr.is_id)
            sat_child.appendChild(transponder_child)
        root.appendChild(sat_child)
    doc.writexml(open(data_path, "w"),
                 # indent="",
                 addindent="    ",
                 newl='\n',
                 encoding="iso-8859-1")
    doc.unlink()


def parse_transponders(elem, sat_name):
    """ Parsing satellite transponders. """
    transponders = []
    for el in elem.getElementsByTagName("transponder"):
        if el.hasAttributes():
            atr = el.attributes
            try:
                tr = Transponder(atr["frequency"].value,
                                 atr["symbol_rate"].value,
                                 POLARIZATION[atr["polarization"].value],
                                 FEC[atr["fec_inner"].value],
                                 SYSTEM[atr["system"].value],
                                 MODULATION[atr["modulation"].value],
                                 atr["pls_mode"].value if "pls_mode" in atr else None,
                                 atr["pls_code"].value if "pls_code" in atr else None,
                                 atr["is_id"].value if "is_id" in atr else None)
            except Exception as e:
                message = "Error: can't parse transponder for '{}' satellite! {}".format(sat_name, repr(e))
                log(message)
            else:
                transponders.append(tr)
    return transponders


def parse_sat(elem):
    """ Parsing satellite. """
    sat_name = elem.attributes["name"].value
    return Satellite(sat_name,
                     elem.attributes["flags"].value,
                     elem.attributes["position"].value,
                     parse_transponders(elem, sat_name))


def is_transponder_valid(tr: Transponder):
    """ Checks  transponder validity. """
    try:
        int(tr.frequency)
        int(tr.symbol_rate)
        tr.pls_mode is None or int(tr.pls_mode)
        tr.pls_code is None or int(tr.pls_code)
        tr.is_id is None or int(tr.is_id)
    except TypeError:
        return False

    if tr.polarization not in POLARIZATION.values():
        return False
    if tr.fec_inner not in FEC.values():
        return False
    if tr.system not in SYSTEM.values():
        return False
    if tr.modulation not in MODULATION.values():
        return False

    return True


def get_key_by_value(dc: dict, value):
    """ Returns key from dict by value. """
    for k, v in dc.items():
        if v == value:
            return k


if __name__ == "__main__":
    pass
