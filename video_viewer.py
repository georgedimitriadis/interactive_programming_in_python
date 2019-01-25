#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, QUrl, QPoint, QTime, QTimer
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QLineEdit,
                             QPushButton, QSlider, QMessageBox, QStyle, QVBoxLayout,
                             QWidget, QShortcut)
import sys

import uuid

import constants as ct

open_windows = {}


class VideoPlayer(QWidget):

    def __init__(self, repl_globals=None, position_var_name=None, file_name_var_name=None, parent=None):
        super(VideoPlayer, self).__init__(parent)

        self.uuid = uuid.uuid4()

        self.repl_globals = repl_globals
        self.position_var_name = position_var_name
        self.file_name_var_name = file_name_var_name
        self.frame_position = self.repl_globals[self.position_var_name]

        self.setGeometry(100, 300, 600, 380)

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start(ct.TIMER_UPDATE_TIME_MILLIS)

        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAcceptDrops(True)
        self.media_player = QMediaPlayer(None, QMediaPlayer.StreamPlayback)
        self.media_player.setVolume(80)
        self.video_widget = QVideoWidget(self)

        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.stateChanged.connect(self.on_media_state_changed)
        self.media_player.positionChanged.connect(self.on_position_change)
        self.media_player.positionChanged.connect(self.handle_label)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.error.connect(self.handle_error)

        self.frame_viewer = QLineEdit(str(self.media_player.position()))
        self.frame_viewer.setReadOnly(True)
        self.frame_viewer.setFixedWidth(70)
        self.frame_viewer.setUpdatesEnabled(True)
        self.frame_viewer.setStyleSheet(stylesheet(self))

        self.time_viewer = QLineEdit('00:00:00')
        self.time_viewer.setReadOnly(True)
        self.time_viewer.setFixedWidth(70)
        self.time_viewer.setUpdatesEnabled(True)
        self.time_viewer.setStyleSheet(stylesheet(self))

        self.full_time_viewer = QLineEdit('00:00:00')
        self.full_time_viewer.setReadOnly(True)
        self.full_time_viewer.setFixedWidth(70)
        self.full_time_viewer.setUpdatesEnabled(True)
        self.full_time_viewer.setStyleSheet(stylesheet(self))

        self.playButton = QPushButton()
        self.playButton.setFixedWidth(32)
        self.playButton.setStyleSheet("background-color: black")
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.position_slider = QSlider(Qt.Horizontal, self)
        self.position_slider.setStyleSheet(stylesheet(self))
        self.position_slider.setRange(0, 100)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.position_slider.sliderMoved.connect(self.handle_label)
        self.position_slider.setSingleStep(1)
        self.position_slider.setPageStep(20)
        self.position_slider.setAttribute(Qt.WA_TranslucentBackground, True)

        slider_controls_layout = QHBoxLayout()
        slider_controls_layout.setContentsMargins(5, 0, 5, 0)
        slider_controls_layout.addWidget(self.playButton)
        slider_controls_layout.addWidget(self.frame_viewer)
        slider_controls_layout.addWidget(self.time_viewer)
        slider_controls_layout.addWidget(self.position_slider)
        slider_controls_layout.addWidget(self.full_time_viewer)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video_widget)
        layout.addLayout(slider_controls_layout)

        self.setLayout(layout)

        self.myinfo = "©2019\nGeorge Dimitriadis\n\nMouse Wheel = Zoom\nUP = Volume Up\nDOWN = Volume Down\n" + \
                      "LEFT = < 1 Minute\nRIGHT = > 1 Minute\n" + \
                      "SHIFT+LEFT = < 10 Minutes\nSHIFT+RIGHT = > 10 Minutes"

        #### shortcuts ####
        self.shortcut = QShortcut(QKeySequence("q"), self)
        self.shortcut.activated.connect(self.handle_quit)
        self.shortcut = QShortcut(QKeySequence(" "), self)
        self.shortcut.activated.connect(self.play)
        self.shortcut = QShortcut(QKeySequence("f"), self)
        self.shortcut.activated.connect(self.handle_fullscreen)
        self.shortcut = QShortcut(QKeySequence("i"), self)
        self.shortcut.activated.connect(self.handle_info)
        self.shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.shortcut.activated.connect(self.forward_slider)
        self.shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.shortcut.activated.connect(self.back_slider)
        self.shortcut = QShortcut(QKeySequence(Qt.Key_Up), self)
        self.shortcut.activated.connect(self.volume_up)
        self.shortcut = QShortcut(QKeySequence(Qt.Key_Down), self)
        self.shortcut.activated.connect(self.volume_down)
        self.shortcut = QShortcut(QKeySequence(Qt.ShiftModifier + Qt.Key_Right), self)
        self.shortcut.activated.connect(self.forward_slider_10)
        self.shortcut = QShortcut(QKeySequence(Qt.ShiftModifier + Qt.Key_Left), self)
        self.shortcut.activated.connect(self.back_slider_10)

        self.widescreen = True
        self.setAcceptDrops(True)
        self.load_film(self.repl_globals[self.file_name_var_name])

    def on_position_change(self, position):
        self.position_slider.setValue(position)
        self.repl_globals[self.position_var_name] = position

    def play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def on_media_state_changed(self, state):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay))

    def on_duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        mtime = QTime(0, 0, 0, 0)
        mtime = mtime.addMSecs(self.media_player.duration())
        self.full_time_viewer.setText(mtime.toString())

    def set_position(self, position):
        self.media_player.setPosition(position)
        self.media_player.pause()

    def handle_error(self):
        self.playButton.setEnabled(False)
        print("Error: ", self.media_player.errorString())

    def handle_quit(self):
        self.media_player.stop()
        del open_windows[self.uuid]
        self.close()

    def closeEvent(self, event):
        self.handle_quit()
        event.accept()

    def handle_fullscreen(self):
        if self.windowState() & Qt.WindowFullScreen:
            self.showNormal()
            print("no Fullscreen")
        else:
            self.showFullScreen()
            print("Fullscreen entered")

    def handle_info(self):
        msg = QMessageBox.about(self, "QT5 Player", self.myinfo)

    def forward_slider(self):
        self.media_player.setPosition(self.media_player.position() + 1000 * 60)

    def forward_slider_10(self):
        self.media_player.setPosition(self.media_player.position() + 10000 * 60)

    def back_slider(self):
        self.media_player.setPosition(self.media_player.position() - 1000 * 60)

    def back_slider_10(self):
        self.media_player.setPosition(self.media_player.position() - 10000 * 60)

    def volume_up(self):
        self.media_player.setVolume(self.media_player.volume() + 10)
        print("Volume: " + str(self.media_player.volume()))

    def volume_down(self):
        self.media_player.setVolume(self.media_player.volume() - 10)
        print("Volume: " + str(self.media_player.volume()))

    def load_film(self, f):
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(f)))
        self.playButton.setEnabled(True)
        self.media_player.pause()

    def handle_label(self):
        self.time_viewer.clear()
        mtime = QTime(0, 0, 0, 0)
        self.time = mtime.addMSecs(self.media_player.position())
        self.time_viewer.setText(self.time.toString())
        self.frame_viewer.setText(str(self.media_player.position()))

    def on_timer_tick(self):
        if self.media_player.state() != QMediaPlayer.PlayingState:
            self.media_player.setPosition(self.repl_globals[self.position_var_name])

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() \
                      - QPoint(self.frameGeometry().width() / 2, \
                               self.frameGeometry().height() / 2))
            event.accept()


###################################################################


def stylesheet(self):
    return """
QSlider::handle:horizontal 
{
background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #333, stop:1 #555555);
width: 14px;
border-radius: 0px;
}
QSlider::groove:horizontal {
border: 1px solid #444;
height: 10px;
background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #000, stop:1 #222222);
}
QLineEdit
{
background: black;
color: #585858;
border: 0px solid #076100;
font-size: 8pt;
font-weight: bold;
}
    """

if QApplication.instance() is None:
    app = QApplication(sys.argv)

windows = []


    #player.setContextMenuPolicy(Qt.CustomContextMenu);
    #player.customContextMenuRequested[QPoint].connect(player.contextMenuRequested)

#sys.exit(app.exec_())


def video(repl_globals, position_var_name, file_name_var_name):
    win = VideoPlayer(repl_globals=repl_globals, position_var_name=position_var_name,
                      file_name_var_name=file_name_var_name)
    open_windows[win.uuid] = win
    win.show()
