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


import sys
from abc import ABC, abstractmethod

from app.commons import log


class Player(ABC):
    """ Base player class. Also used as a factory. """

    @abstractmethod
    def play(self, mrl=None):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def set_time(self, time):
        pass

    @abstractmethod
    def release(self):
        pass

    @abstractmethod
    def is_playing(self):
        pass

    @abstractmethod
    def get_instance(self, mode, widget, buf_cb, position_cb, error_cb, playing_cb):
        pass

    @staticmethod
    def make(name, widget, buf_cb=None, position_cb=None, error_cb=None, playing_cb=None):
        """ Factory method. We will not use a separate factory to return a specific implementation.

            @param name: implementation name.
            @param widget: media widget.
            @param buf_cb: buffering callback.
            @param position_cb: time (position) callback.
            @param error_cb: error callback.
            @param playing_cb: playing state callback.

            Throws a NameError if there is no implementation for the given name.
        """
        if name == "MPV":
            return MpvPlayer.get_instance(widget, buf_cb, position_cb, error_cb, playing_cb)
        elif name == "VLC":
            return VlcPlayer.get_instance(widget, buf_cb, position_cb, error_cb, playing_cb)
        else:
            raise NameError("There is no such [{}] implementation.".format(name))


class MpvPlayer(Player):
    """ Simple wrapper for MPV media player.

        Uses python-mvp [https://github.com/jaseg/python-mpv].
    """
    __INSTANCE = None

    def __init__(self, widget, buf_cb, position_cb, error_cb, playing_cb):
        try:
            from app.streams import mpv

            self._player = mpv.MPV(wid=str(int(widget.winId())),
                                   input_default_bindings=False,
                                   input_cursor=False,
                                   cursor_autohide="no")
        except OSError as e:
            log("{}: Load library error: {}".format(__class__.__name__, e))
            raise ImportError("No libmpv is found. Check that it is installed!")
        else:
            self._is_playing = False

            @self._player.event_callback(mpv.MpvEventID.FILE_LOADED)
            def on_open(event):
                log("Starting playback...")
                if playing_cb:
                    playing_cb()

            @self._player.event_callback(mpv.MpvEventID.END_FILE)
            def on_end(event):
                event = event.get("event", {})
                if event.get("reason", mpv.MpvEventEndFile.ERROR) == mpv.MpvEventEndFile.ERROR:
                    log("Stream playback error: {}".format(event.get("error", mpv.ErrorCode.GENERIC)))
                    if error_cb:
                        error_cb()

    @classmethod
    def get_instance(cls, widget, buf_cb, position_cb, error_cb, playing_cb):
        if not cls.__INSTANCE:
            cls.__INSTANCE = MpvPlayer(widget, buf_cb, position_cb, error_cb, playing_cb)
        return cls.__INSTANCE

    def play(self, mrl=None):
        if not mrl:
            return

        self._player.play(mrl)
        self._is_playing = True

    def stop(self):
        self._player.stop()
        self._is_playing = True

    def pause(self):
        pass

    def set_time(self, time):
        pass

    def release(self):
        self._player.terminate()
        self.__INSTANCE = None

    def is_playing(self):
        return self._is_playing


class VlcPlayer(Player):
    """ Simple wrapper for VLC media player.

        Uses python-vlc [https://github.com/oaubert/python-vlc].
    """

    __VLC_INSTANCE = None

    def __init__(self, widget, buf_cb, position_cb, error_cb, playing_cb):
        try:
            from app.streams import vlc
            from app.streams.vlc import EventType

            args = "--quiet {}".format("" if sys.platform == "darwin" else "--no-xlib")
            self._player = vlc.Instance(args).media_player_new()
            vlc.libvlc_video_set_key_input(self._player, False)
            vlc.libvlc_video_set_mouse_input(self._player, False)
        except (OSError, AttributeError, NameError) as e:
            log("{}: Load library error: {}".format(__class__.__name__, e))
            raise ImportError("No VLC is found. Check that it is installed!")
        else:
            self._is_playing = False

            ev_mgr = self._player.event_manager()

            if buf_cb:
                # TODO look other EventType options
                ev_mgr.event_attach(EventType.MediaPlayerBuffering,
                                    lambda et, p: buf_cb(p.get_media().get_duration()),
                                    self._player)
            if position_cb:
                ev_mgr.event_attach(EventType.MediaPlayerTimeChanged,
                                    lambda et, p: position_cb(p.get_time()),
                                    self._player)

            if error_cb:
                ev_mgr.event_attach(EventType.MediaPlayerEncounteredError,
                                    lambda et, p: error_cb(),
                                    self._player)
            if playing_cb:
                ev_mgr.event_attach(EventType.MediaPlayerPlaying,
                                    lambda et, p: playing_cb(),
                                    self._player)

            self.init_video_widget(widget)

    @classmethod
    def get_instance(cls, widget, buf_cb=None, position_cb=None, error_cb=None, playing_cb=None):
        if not cls.__VLC_INSTANCE:
            cls.__VLC_INSTANCE = VlcPlayer(widget, buf_cb, position_cb, error_cb, playing_cb)
        return cls.__VLC_INSTANCE

    def play(self, mrl=None):
        if mrl:
            self._player.set_mrl(mrl)
        self._player.play()
        self._is_playing = True

    def stop(self):
        if self._is_playing:
            self._player.stop()
            self._is_playing = False

    def pause(self):
        self._player.pause()

    def set_time(self, time):
        self._player.set_time(time)

    def release(self):
        if self._player:
            self._is_playing = False
            self._player.stop()
            self._player.release()
            self.__VLC_INSTANCE = None

    def set_mrl(self, mrl):
        self._player.set_mrl(mrl)

    def is_playing(self):
        return self._is_playing

    def init_video_widget(self, widget):
        win_id = int(widget.winId())
        if sys.platform == "linux":
            self._player.set_xwindow(win_id)
        elif sys.platform == "darwin":
            self._player.set_nsobject(win_id)
        else:
            self._player.set_hwnd(win_id)


if __name__ == "__main__":
    pass
