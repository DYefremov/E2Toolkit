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


import os
import re
import socket
import time
import xml.etree.ElementTree as ETree
from enum import Enum
from ftplib import FTP, Error, CRLF, error_perm
from telnetlib import Telnet
from urllib.parse import urlencode

from PyQt5.QtCore import QUrl, QThread, pyqtSignal
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QSslSocket, QSslConfiguration, QNetworkReply

from app.commons import log

# ******************* FTP ********************** #

BQ_FILES_LIST = ("tv", "radio")
DATA_FILES_LIST = ("lamedb", "lamedb5", "blacklist", "whitelist",)
STC_XML_FILE = ("satellites.xml", "terrestrial.xml", "cables.xml")
PICONS_SUF = (".jpg", ".png")


class DownloadType(Enum):
    ALL = 0
    BOUQUETS = 1
    SATELLITES = 2
    PICONS = 3
    EPG = 4


class DataLoader(QThread):
    """ Data load helper class.

        Loads data in a separate thread.
    """
    message = pyqtSignal(str)
    error_message = pyqtSignal(str)
    loaded = pyqtSignal(DownloadType)

    def __init__(self, settings, download_type=DownloadType.ALL, upload=False, files_filter=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = settings
        self.download_type = download_type
        self.upload = upload
        self.file_filter = files_filter
        self.finished.connect(lambda: self.loaded.emit(self.download_type))

    def run(self):
        if self.upload:
            pass
        else:
            try:
                download_data(settings=self.settings,
                              download_type=self.download_type,
                              callback=self.message.emit,
                              files_filter=self.file_filter)
            except Exception as e:
                error_msg = "Error: {}".format(str(e))
                self.error_message.emit(error_msg)
                self.message.emit(error_msg)


class UtfFTP(FTP):
    """ FTP class wrapper. """

    def retrlines(self, cmd, callback=None):
        """ Small modification of the original method.

            It is used to retrieve data in line mode and skip errors related
            to reading file names in encoding other than UTF-8 or Latin-1.
            Decode errors are ignored [UnicodeDecodeError, etc].
         """
        if callback is None:
            callback = log
        self.sendcmd("TYPE A")
        with self.transfercmd(cmd) as conn, conn.makefile("r", encoding=self.encoding, errors="ignore") as fp:
            while 1:
                line = fp.readline(self.maxline + 1)
                if len(line) > self.maxline:
                    msg = "UtfFTP [retrlines] error: got more than {} bytes".format(self.maxline)
                    log(msg)
                    raise Error(msg)
                if self.debugging > 2:
                    log('UtfFTP [retrlines] *retr* {}'.format(repr(line)))
                if not line:
                    break
                if line[-2:] == CRLF:
                    line = line[:-2]
                elif line[-1:] == "\n":
                    line = line[:-1]
                callback(line)
        return self.voidresp()

    # ***************** Download ******************* #

    def download_files(self, save_path, file_list, callback=None):
        """ Downloads files from the receiver via FTP. """
        for file in filter(lambda s: s.endswith(file_list), self.nlst()):
            self.download_file(file, save_path, callback)

    def download_file(self, name, save_path, callback=None):
        with open(save_path + name, "wb") as f:
            msg = "Downloading file: {}.   Status: {}"
            try:
                resp = str(self.retrbinary("RETR " + name, f.write))
            except error_perm as e:
                resp = str(e)
                msg = msg.format(name, e)
                log(msg.rstrip())
            else:
                msg = msg.format(name, resp)

            callback(msg) if callback else log(msg.rstrip())

            return resp

    def download_dir(self, path, save_path, callback=None):
        """  Downloads directory from FTP with all contents.

            Creates a leaf directory and all intermediate ones. This is recursive.
         """
        os.makedirs(os.path.join(save_path, path), exist_ok=True)

        files = []
        self.dir(path, files.append)
        for f in files:
            f_data = f.split()
            f_path = os.path.join(path, " ".join(f_data[8:]))

            if f_data[0][0] == "d":
                try:
                    os.makedirs(os.path.join(save_path, f_path), exist_ok=True)
                except OSError as e:
                    msg = "Download dir error: {}".format(e).rstrip()
                    log(msg)
                    return "500 " + msg
                else:
                    self.download_dir(f_path, save_path, callback)
            else:
                try:
                    self.download_file(f_path, save_path, callback)
                except OSError as e:
                    log("Download dir error: {}".format(e).rstrip())

        resp = "226 Transfer complete."
        msg = "Copy directory {}.   Status: {}".format(path, resp)
        log(msg)

        if callback:
            callback(msg)

        return resp

    def download_xml(self, data_path, xml_path, xml_files, callback):
        """ Used for download *.xml files. """
        self.cwd(xml_path)
        self.download_files(data_path, xml_files, callback)

    def download_picons(self, src, dest, callback, files_filter=None):
        try:
            self.cwd(src)
        except error_perm as e:
            callback(str(e))
            return

        for file in filter(picons_filter_function(files_filter), self.nlst()):
            self.download_file(file, dest, callback)

    # ***************** Uploading ******************* #

    def upload_bouquets(self, data_path, remove_unused, callback):
        if remove_unused:
            self.remove_unused_bouquets(callback)
        self.upload_files(data_path, BQ_FILES_LIST, callback)

    def upload_files(self, data_path, file_list, callback):
        for file_name in os.listdir(data_path):
            if file_name in STC_XML_FILE:
                continue
            if file_name.endswith(file_list):
                self.send_file(file_name, data_path, callback)

    def upload_xml(self, data_path, xml_path, xml_files, callback):
        """ Used for transfer *.xml files. """
        self.cwd(xml_path)
        for xml_file in xml_files:
            self.send_file(xml_file, data_path, callback)

    def upload_picons(self, src, dest, callback, files_filter=None):
        try:
            self.cwd(dest)
        except error_perm as e:
            if str(e).startswith("550"):
                self.mkd(dest)  # if not exist
                self.cwd(dest)

        for file_name in filter(picons_filter_function(files_filter), os.listdir(src)):
            self.send_file(file_name, src, callback)

    def remove_unused_bouquets(self, callback):
        bq_files = ("userbouquet.", "bouquets.xml", "ubouquets.xml")

        for file in filter(lambda f: f.startswith(bq_files), self.nlst()):
            self.delete_file(file, callback)

    def send_file(self, file_name, path, callback=None):
        """ Opens the file in binary mode and transfers into receiver """
        file_src = path + file_name
        resp = "500"
        if not os.path.isfile(file_src):
            log("Uploading file: '{}'. File not found. Skipping.".format(file_src))
            return resp + " File not found."

        with open(file_src, "rb") as f:
            msg = "Uploading file: {}.   Status: {}\n"
            try:
                resp = str(self.storbinary("STOR " + file_name, f))
            except Error as e:
                resp = str(e)
                msg = msg.format(file_name, resp)
                log(msg)
            else:
                msg = msg.format(file_name, resp)

            if callback:
                callback(msg)

        return resp

    def upload_dir(self, path, callback=None):
        """ Uploads directory to FTP with all contents.

            Creates a leaf directory and all intermediate ones. This is recursive.
        """
        resp = "200"
        msg = "Uploading directory: {}.   Status: {}"
        try:
            files = os.listdir(path)
        except OSError as e:
            log(e)
        else:
            os.chdir(path)
            for f in files:
                file = r"{}{}".format(path, f)
                if os.path.isfile(file):
                    self.send_file(f, path, callback)
                elif os.path.isdir(file):
                    try:
                        self.mkd(f)
                    except Error:
                        pass  # NOP

                    try:
                        self.cwd(f)
                    except Error as e:
                        resp = str(e)
                        log(msg.format(f, resp))
                    else:
                        self.upload_dir(file + "/")

            self.cwd("..")
            os.chdir("..")

            if callback:
                callback(msg.format(path, resp))

        return resp

    # ****************** Deletion ******************** #

    def delete_picons(self, callback, dest=None, files_filter=None):
        if dest:
            try:
                self.cwd(dest)
            except Error as e:
                callback(str(e))
                return

        for file in filter(picons_filter_function(files_filter), self.nlst()):
            self.delete_file(file, callback)

    def delete_file(self, file, callback=log):
        msg = "Deleting file: {}.   Status: {}\n"
        try:
            resp = self.delete(file)
        except Error as e:
            resp = str(e)
            msg = msg.format(file, resp)
            log(msg)
        else:
            msg = msg.format(file, resp)

        if callback:
            callback(msg)

        return resp

    def delete_dir(self, path, callback=None):
        files = []
        self.dir(path, files.append)
        for f in files:
            f_data = f.split()
            name = " ".join(f_data[8:])
            f_path = path + "/" + name

            if f_data[0][0] == "d":
                self.delete_dir(f_path, callback)
            else:
                self.delete_file(f_path, callback)

        msg = "Remove directory {}.   Status: {}\n"
        try:
            resp = self.rmd(path)
        except Error as e:
            msg = msg.format(path, e)
            log(msg)
            return "500"
        else:
            msg = msg.format(path, resp)
            log(msg.rstrip())

        if callback:
            callback(msg)

        return resp

    def rename_file(self, from_name, to_name, callback=None):
        msg = "File rename: {}.   Status: {}\n"
        try:
            resp = self.rename(from_name, to_name)
        except Error as e:
            resp = str(e)
            msg = msg.format(from_name, resp)
            log(msg)
        else:
            msg = msg.format(from_name, resp)

        if callback:
            callback(msg)

        return resp


def download_data(*, settings, download_type=DownloadType.ALL, callback=log, files_filter=None):
    profile = settings.current_profile
    save_path = "{}{}{}".format(settings.data_path, profile["name"], os.sep)

    with UtfFTP(host=profile["host"], user=profile["user"], passwd=profile["password"]) as ftp:
        ftp.encoding = "utf-8"
        callback("FTP OK.")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        # Bouquets
        if download_type is DownloadType.ALL or download_type is DownloadType.BOUQUETS:
            ftp.cwd(settings.box_services_path)
            file_list = BQ_FILES_LIST + DATA_FILES_LIST if download_type is DownloadType.ALL else BQ_FILES_LIST
            ftp.download_files(save_path, file_list, callback)
        # *.xml
        if download_type in (DownloadType.ALL, DownloadType.SATELLITES):
            ftp.download_xml(save_path, settings.box_satellite_path, STC_XML_FILE, callback)

        if download_type is DownloadType.PICONS:
            picons_local_path = "{}{}{}".format(settings.picon_path, settings.current_profile["name"], os.sep)
            os.makedirs(os.path.dirname(picons_local_path), exist_ok=True)
            ftp.download_picons(settings.current_profile["box_picon_path"], picons_local_path, callback, files_filter)
        # epg.dat
        if download_type is DownloadType.EPG:
            log("Not implemented yet!")
            raise OSError("Not implemented yet!")

        callback("Done.")


def upload_data(*, settings, download_type=DownloadType.ALL, remove_unused=False,
                callback=log, done_callback=None, http=None, files_filter=None):
    data_path = settings.data_local_path
    host = settings.host
    tn = None  # telnet

    try:
        if http:
            message = ""
            if download_type is DownloadType.BOUQUETS:
                message = "User bouquets will be updated!"
            elif download_type is DownloadType.ALL:
                message = "All user data will be reloaded!"
            elif download_type is DownloadType.SATELLITES:
                message = "Satellites.xml file will be updated!"
            elif download_type is DownloadType.PICONS:
                message = "Picons will be updated!"

            params = urlencode({"text": message, "type": 2, "timeout": 5})
            http.send(("message?{}".format(params), "Sending info message..."))

            if download_type is DownloadType.ALL:
                time.sleep(5)
                http.send(("powerstate?newstate=0", "Toggle Standby"))
                time.sleep(2)
        else:
            if download_type is not DownloadType.PICONS:
                # telnet
                tn = telnet(host=host,
                            user=settings.user,
                            password=settings.password,
                            timeout=settings.telnet_timeout)
                next(tn)
                # terminate Enigma2
                callback("Telnet initialization ...\n")
                tn.send("init 4")
                callback("Stopping GUI...\n")

        with UtfFTP(host=host, user=settings.user, passwd=settings.password) as ftp:
            ftp.encoding = "utf-8"
            callback("FTP OK.\n")
            sat_xml_path = settings.satellites_xml_path
            services_path = settings.services_path

            if download_type is DownloadType.SATELLITES:
                ftp.upload_xml(data_path, sat_xml_path, STC_XML_FILE, callback)

            if download_type is DownloadType.BOUQUETS:
                ftp.cwd(services_path)
                ftp.upload_bouquets(data_path, remove_unused, callback)

            if download_type is DownloadType.ALL:
                ftp.upload_xml(data_path, sat_xml_path, STC_XML_FILE, callback)
                ftp.cwd(services_path)
                ftp.upload_bouquets(data_path, remove_unused, callback)
                ftp.upload_files(data_path, DATA_FILES_LIST, callback)

            if download_type is DownloadType.PICONS:
                ftp.upload_picons(settings.picons_local_path, settings.picons_path, callback, files_filter)

            if tn and not http:
                # resume enigma
                tn.send("init 3")
                callback("Starting...\n")
            elif http:
                if download_type is DownloadType.BOUQUETS:
                    http.send(("servicelistreload?mode=2", "Reloading Userbouquets."))
                elif download_type is DownloadType.ALL:
                    http.send(("servicelistreload?mode=0", "Reloading lamedb and Userbouquets."))
                    http.send(("powerstate?newstate=4", "Wakeup from Standby."))

            if done_callback is not None:
                done_callback()
    finally:
        if tn:
            tn.close()


# ***************** Picons ******************* #

def remove_picons(*, settings, callback, done_callback=None, files_filter=None):
    """ Removes picons from the Box via FTP. """
    with UtfFTP(host=settings.host, user=settings.user, passwd=settings.password) as ftp:
        ftp.encoding = "utf-8"
        callback("FTP OK.\n")
        ftp.delete_picons(callback, settings.picons_path, files_filter)
        if done_callback:
            done_callback()


def picons_filter_function(files_filter=None):
    return lambda f: f in files_filter if files_filter else f.endswith(PICONS_SUF)


# ***************** HTTP API ******************* #

class HttpAPI:
    """ Core HTTP class.

        This is a holder (wrapper) for aiohttp.ClientSession class.
     """

    class Request(str, Enum):
        ZAP = "zap?sRef="
        INFO = "about"
        SIGNAL = "signal"
        STREAM = "stream.m3u?ref="
        STREAM_CURRENT = "streamcurrent.m3u"
        CURRENT = "getcurrent"
        TEST = None
        POWER_STATE = "powerstate"
        TOKEN = "session"
        # Player
        PLAY = "mediaplayerplay?file="
        PLAYER_LIST = "mediaplayerlist?path=playlist"
        PLAYER_PLAY = "mediaplayercmd?command=play"
        PLAYER_NEXT = "mediaplayercmd?command=next"
        PLAYER_PREV = "mediaplayercmd?command=previous"
        PLAYER_STOP = "mediaplayercmd?command=stop"
        PLAYER_REMOVE = "mediaplayerremove?file="
        # Remote control
        POWER = "powerstate?newstate="
        REMOTE = "remotecontrol?command="
        VOL = "vol?set=set"
        # EPG
        EPG = "epgservice?sRef="
        # Timer
        TIMER = ""
        TIMER_LIST = "timerlist"
        # Screenshot
        GRUB = "grab?format=jpg&"

    class Remote(str, Enum):
        """ Args for HttpRequestType [REMOTE] class. """
        UP = "103"
        LEFT = "105"
        RIGHT = "106"
        DOWN = "108"
        MENU = "139"
        EXIT = "174"
        OK = "352"
        RED = "398"
        GREEN = "399"
        YELLOW = "400"
        BLUE = "401"

    class Power(str, Enum):
        """ Args for HttpRequestType [POWER] class. """
        TOGGLE_STANDBY = "0"
        DEEP_STANDBY = "1"
        REBOOT = "2"
        RESTART_GUI = "3"
        WAKEUP = "4"
        STANDBY = "5"

    def __init__(self, settings, callbacks={}):
        host, use_ssl, port = settings["host"], settings["http_use_ssl"], settings["http_port"]
        self._main_url = "http{}://{}:{}/web/".format("s" if use_ssl else "", host, port)
        self._settings = settings
        self._use_ssl = use_ssl
        self._callbacks = callbacks
        # SSL
        self._ssl_config = QSslConfiguration.defaultConfiguration()
        self._ssl_config.setPeerVerifyMode(QSslSocket.VerifyNone)
        # Manager
        self._auth = 0
        self._token = b"sessionid=0"
        self.network_manager = QNetworkAccessManager()
        self.network_manager.authenticationRequired.connect(self.auth)
        self.network_manager.finished.connect(self.handle_response)

    def auth(self, reply, auth):
        self._auth += 1
        if self._auth >= 3:
            reply.abort()

        auth.setUser(self._settings["user"])
        auth.setPassword(self._settings["password"])
        # Token
        self._callbacks[self.Request.TOKEN] = self.set_token
        self.send(self.Request.TOKEN)

    def send(self, req, params=None):
        request = QNetworkRequest(QUrl("{}{}{}".format(self._main_url, req, params if params else "")))
        request.setSslConfiguration(self._ssl_config)
        request.setAttribute(request.CustomVerbAttribute, req)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded")
        self.network_manager.post(request, self._token)

    def handle_response(self, reply):
        req = reply.request().attribute(QNetworkRequest.CustomVerbAttribute)
        callback = self._callbacks.get(req)
        er = reply.error()
        if not callback:
            return

        if er == QNetworkReply.NoError:
            if req is HttpAPI.Request.STREAM or type is HttpAPI.Request.STREAM_CURRENT:
                callback({"m3u": reply.readAll()})
            elif req is HttpAPI.Request.GRUB:
                callback({"img_data": reply.readAll()})
            elif req is HttpAPI.Request.CURRENT:
                for el in ETree.parse(reply).iter("e2event"):
                    callback({el.tag: el.text for el in el.iter()})  # first[current] event from the list
            elif req is HttpAPI.Request.PLAYER_LIST:
                callback([{el.tag: el.text for el in el.iter()} for el in ETree.parse(reply).iter("e2file")])
            elif req is HttpAPI.Request.EPG:
                callback({"event_list": [{el.tag: el.text for el in el.iter()} for el in
                                         ETree.parse(reply).iter("e2event")]})
            elif req is HttpAPI.Request.TIMER_LIST:
                callback({"timer_list": [{el.tag: el.text for el in el.iter()} for el in
                                         ETree.parse(reply).iter("e2timer")]})
            else:
                callback({el.tag: el.text for el in ETree.parse(reply).iter()})

        else:
            callback({"error": -1, "reason": reply.errorString()})

    def append_callback(self, req, callback):
        self._callbacks[req] = callback

    def set_token(self, data):
        self._token = "sessionid={}".format(data.get("e2sessionid", "0")).encode()


# ******************* Telnet ********************* #

def telnet(host, port=23, user="", password="", timeout=5):
    try:
        tn = Telnet(host=host, port=port, timeout=timeout)
    except socket.timeout:
        log("telnet error: socket timeout")
    else:
        time.sleep(1)
        command = yield
        if user != "":
            tn.read_until(b"login: ", timeout)
            tn.write(user.encode("utf-8") + b"\n")
            time.sleep(timeout)
        if password != "":
            tn.read_until(b"Password: ", timeout)
            tn.write(password.encode("utf-8") + b"\n")
            time.sleep(timeout)
        tn.write("{}\r\n".format(command).encode("utf-8"))
        time.sleep(timeout)
        command = yield
        time.sleep(timeout)
        tn.write("{}\r\n".format(command).encode("utf-8"))
        time.sleep(timeout)
        yield


# *************** Connections testing. ************* #

class TestException(Exception):
    pass


def test_ftp(host, port, user, password, timeout=5):
    try:
        with FTP(host=host, user=user, passwd=password, timeout=timeout) as ftp:
            return ftp.getwelcome()
    except (error_perm, ConnectionRefusedError, OSError) as e:
        raise TestException(e)


def test_telnet(host, port, user, password, timeout=5):
    try:
        gen = telnet_test(host, port, user, password, timeout)
        res = next(gen)
        msg = str(res, encoding="utf8").strip()
        log(msg)
        next(gen)
        if re.search("password", msg, re.IGNORECASE):
            raise TestException(msg)
        return msg
    except (socket.timeout, OSError) as e:
        raise TestException(e)


def telnet_test(host, port, user, password, timeout):
    tn = Telnet(host=host, port=port, timeout=timeout)
    time.sleep(1)
    tn.read_until(b"login: ", timeout=2)
    tn.write(user.encode("utf-8") + b"\r")
    time.sleep(timeout)
    tn.read_until(b"Password: ", timeout=2)
    tn.write(password.encode("utf-8") + b"\r")
    time.sleep(timeout)
    yield tn.read_very_eager()
    tn.close()
    yield


if __name__ == "__main__":
    pass
