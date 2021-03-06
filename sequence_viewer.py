
import sys
from PyQt5 import QtWidgets, QtCore

import numpy as np
import pyqtgraph as pg
from pyqtgraph.widgets import RawImageWidget

import matplotlib.pyplot as plt

import uuid

import cv2

import constants as ct

open_windows = {}


class AbstractSequencerGUI(QtWidgets.QWidget):
    def __init__(self):
        # call super class constructor
        super(AbstractSequencerGUI, self).__init__()

        self.uuid = uuid.uuid4()
        self.repl_globals = None
        self.plotted_y_variable_name = None
        self.plotted_x_variable_name = None
        self.tracker_variable_name = None
        self.index = None
        self.max_index = None
        self.min_index = 0
        self.data = None
        self.x_axis = None
        self.text_is_being_edited = False
        self.transform_name = None
        self.transform = None

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start(ct.TIMER_UPDATE_TIME_MILLIS)

        self.layout_window = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout_window)
        self.buttons_layout = QtWidgets.QHBoxLayout()

        self.button_fwd = QtWidgets.QPushButton('FWD')
        self.button_fwd.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowForward))
        self.button_fwd.clicked.connect(self.on_button_forwards)

        self.button_bwd = QtWidgets.QPushButton('BWD')
        self.button_bwd.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowBack))
        self.button_bwd.clicked.connect(self.on_button_backwards)

        self.label_position = QtWidgets.QLabel('     POSITION:  ')

        self.edit_text_position = QtWidgets.QLineEdit()
        self.edit_text_position.returnPressed.connect(self.on_new_position)
        self.edit_text_position.textEdited.connect(self.on_position_edited)

        self.slider_position = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_position.valueChanged.connect(self.on_slider_change)
        self.slider_position.setMinimum(self.min_index)
        self.slider_position.setTickInterval(1)
        self.slider_position.setSingleStep(1)

        self.layout_window.insertLayout(-2, self.buttons_layout)
        self.buttons_layout.addWidget(self.button_bwd)
        self.buttons_layout.addWidget(self.button_fwd)
        self.buttons_layout.addSpacing(200)
        self.buttons_layout.addWidget(self.label_position)
        self.buttons_layout.addWidget(self.edit_text_position)
        self.layout_window.insertWidget(-1, self.slider_position)

        self.resize(800, 600)

    def closeEvent(self, event):
        del open_windows[self.uuid]
        self.close()
        event.accept()

    def on_button_forwards(self):
        index = self.repl_globals[self.tracker_variable_name]
        if index < self.max_index:
            self.repl_globals[self.tracker_variable_name] += 1

    def on_button_backwards(self):
        index = self.repl_globals[self.tracker_variable_name]
        if index > self.min_index:
            self.repl_globals[self.tracker_variable_name] -= 1

    def on_new_position(self):
        try:
            new_value = int(self.edit_text_position.text())
            if new_value >= 0 and new_value <= self.max_index:
                self.repl_globals[self.tracker_variable_name] = int(self.edit_text_position.text())
            else:
                print('Input to text window to turn into an index to small or too big')
        except ValueError:
            print('Invalid input to text window to turn into an index')

        self.text_is_being_edited = False

    def on_position_edited(self):
        self.text_is_being_edited = True

    def on_slider_change(self):
        self.repl_globals[self.tracker_variable_name] = int(self.slider_position.value())

    def on_timer_tick(self):
        pass

    def _update_index(self):
        try:
            self.index = self.repl_globals[self.tracker_variable_name]
        except KeyError:
            print('Variable {} to use as index not defined in the REPL'.format(self.tracker_variable_name))
            self.close()

    def _update_text_and_slider(self):
        if self.text_is_being_edited is False:
            self.edit_text_position.setText(str(self.index))
        self.slider_position.setValue(self.index)


class GraphPaneGUI(AbstractSequencerGUI):
    def __init__(self):
        super(GraphPaneGUI, self).__init__()

        self.stepmode = False
        self.fillLevel = None
        self.brush = (255, 255, 255, 255)

        self.plot_widget = pg.PlotWidget()
        self.plot_data_item = pg.PlotDataItem()
        self.plot_widget.addItem(self.plot_data_item)

        self.layout_window.insertWidget(0, self.plot_widget)

    def _load_data(self):
        try:
            temp = self.repl_globals[self.plotted_y_variable_name]
        except KeyError:
            print('Y axis variable to plot {} not defined in the REPL'.format(self.plotted_y_variable_name))
            self.close()

        if type(temp).__name__ == 'memmap':
            self.data = temp[:]
        else:
            self.data = np.array(temp)

        if self.transform_name is not None:
            try:
                self.transform = self.repl_globals[self.transform_name]
            except KeyError:
                print('Transform function {} to push the data through is not defined in the REPL'.format(self.transform_name))
                self.close()

    def _setup_maximum_index_value(self):
        self.max_index = np.shape(self.data)[0] - 1
        self.slider_position.setMaximum(self.max_index)

    def _setup_x_axis(self):
        if self.plotted_x_variable_name is None:
            if len(self.data.shape) == 2:
                self.x_axis = np.arange(self.data.shape[1])
            if len(self.data.shape) == 3:
                self.x_axis = np.tile(np.arange(self.data.shape[2]), self.data.shape[1])
        else:
            try:
                self.x_axis = np.array(self.repl_globals[self.plotted_x_variable_name])
            except KeyError:
                print('X axis variable to plot {} not defined in the REPL'.format(
                    self.plotted_x_variable_name))
                self.close()

            if self.data.shape[-1] == len(self.x_axis):
                self.stepmode = False
                self.fillLevel = None
                self.brush = (255, 255, 255, 255)
            elif self.data.shape[-1] + 1 == len(self.x_axis): # If the x axis is one larger than the y then draw a histogram
                self.stepmode = True
                self.fillLevel = 0
                self.brush = (0, 0, 255, 150)
            else:
                print('X axis length {} needs to be equal (or one larger for a histogram) to data length {}'\
                      .format(self.x_axis.shape[0], self.data.shape[-1]))
                self.close()

            if len(self.data.shape) == 3:
                # Tile so that the x_axis corresponds to data[index, :, :].flatten()
                # example: t = [0,1,2,3] for data.shape=(i, 2, 4) becomes t = [0, 1, 2, 3, 0, 1, 2, 3, 4]
                self.x_axis = np.tile(self.x_axis, self.data.shape[1])

    def _update_plot(self):
        if len(np.shape(self.data)) == 2:
            y = self.data[self.index, :]
            if self.transform is not None:
                y = self.transform(y)
            if self.fillLevel is None:
                self.plot_data_item.setData(self.x_axis, y, stepMode=self.stepmode, brush=self.brush)
            else:
                self.plot_data_item.setData(self.x_axis, y, stepMode=self.stepmode,
                                            fillLevel=self.fillLevel, brush=self.brush)
        elif len(np.shape(self.data)) == 3:
            # The connect argument allows a single line to be broken up (see pg.ArrayToQPath) so that the
            # 1D array data[index, :, :].flatten() shows up as multiple independent lines
            connect = np.ones(len(self.x_axis))
            connect[np.arange(self.data.shape[2] - 1, self.data.shape[2] * self.data.shape[1], self.data.shape[2])] = 0
            self.plot_data_item.opts['connect'] = connect

            y = self.data[self.index, :, :]

            if self.transform is not None:
                y = self.transform(y)

            y = y.flatten()
            self.plot_data_item.setData(self.x_axis, y, pen='k')

    def on_timer_tick(self):
        if self.repl_globals is not None:

            if self.data is None:
                self._load_data()

            if self.max_index is None:
                self._setup_maximum_index_value()

            if self.x_axis is None:
                self._setup_x_axis()

            self._update_index()

            self._update_text_and_slider()

            self._update_plot()


class GraphRangeGUI(GraphPaneGUI):
    def __init__(self):
        super(GraphRangeGUI, self).__init__()

        self.tracker_range_variable_name = None
        self.index_range = None
        self.brush = (0, 0, 0, 255)
        self.range_is_being_edited = False

        self.edit_text_range = QtWidgets.QLineEdit()
        self.edit_text_range.returnPressed.connect(self.on_new_range)
        self.edit_text_range.textEdited.connect(self.on_range_edited)

        self.buttons_layout.addWidget(self.edit_text_range)
        self.buttons_layout.addSpacing(20)

    def on_button_forwards(self):
        index = self.repl_globals[self.tracker_variable_name]
        if index < self.max_index:
            self.repl_globals[self.tracker_variable_name] += self.index_range

    def on_button_backwards(self):
        index = self.repl_globals[self.tracker_variable_name]
        if index - self.index_range > self.min_index:
            self.repl_globals[self.tracker_variable_name] -= self.index_range

    def on_new_range(self):
        try:
            new_value = int(self.edit_text_range.text())
            if new_value >= 0 and new_value <= np.shape(self.data)[-1] - self.index_range:
                self.repl_globals[self.tracker_range_variable_name] = int(self.edit_text_range.text())
            else:
                print('Input to text window to turn into a range, to small or too big')
        except ValueError:
            print('Invalid input to text window to turn into a range')

        self.range_is_being_edited = False

    def on_range_edited(self):
        self.range_is_being_edited = True

    def _update_index(self):
        try:
            self.index = self.repl_globals[self.tracker_variable_name]
        except KeyError:
            print('Variable {} to use as index not defined in the REPL'.format(self.tracker_variable_name))
            self.close()

        try:
            self.index_range = self.repl_globals[self.tracker_range_variable_name]
        except KeyError:
            print('Variable {} to use as index not defined in the REPL'.format(self.tracker_range_variable_name))
            self.close()

    def _setup_maximum_index_value(self):
        self.max_index = np.shape(self.data)[-1] - 1 - self.index_range
        self.slider_position.setMaximum(self.max_index)

    def _setup_x_axis(self):
        if len(self.data.shape) == 1:
            self.x_axis = np.arange(self.index_range)
        if len(self.data.shape) == 2:
            self.x_axis = np.tile(np.arange(self.index_range), self.data.shape[0])

        if self.plotted_x_variable_name is not None:
            try:
                x_axis_multiplier = np.array(self.repl_globals[self.plotted_x_variable_name])
            except KeyError:
                print('X axis multiplier variable {} is not defined in the REPL'.format(
                    self.plotted_x_variable_name))
                self.close()
            self.x_axis = self.x_axis.astype(np.float) * x_axis_multiplier

    def _update_text_and_slider(self):
        if self.text_is_being_edited is False:
            self.edit_text_position.setText(str(self.index))
        self.slider_position.setValue(self.index)

        if self.range_is_being_edited is False:
            self.edit_text_range.setText(str(self.index_range))

    def _update_plot(self):
        if len(np.shape(self.data)) == 1:
            y = self.data[self.index:(self.index + self.index_range)]

            if self.transform is not None:
                y = self.transform(y)

            self.plot_data_item.setData(self.x_axis, y, pen='k')

        elif len(np.shape(self.data)) == 2:
            # The connect argument allows a single line to be broken up (see pg.ArrayToQPath) so that the
            # 1D array data[index, :, :].flatten() shows up as multiple independent lines
            connect = np.ones(len(self.x_axis))

            y = self.data[:, self.index:(self.index + self.index_range)]

            if self.transform is not None:
                y = self.transform(y)

            y = y.flatten()
            connect[np.arange(self.index_range - 1, y.size, self.index_range)] = 0
            self.plot_data_item.opts['connect'] = connect

            self.plot_data_item.setData(self.x_axis, y, pen='k')

    def on_timer_tick(self):
        if self.repl_globals is not None:

            if self.data is None:
                self._load_data()

            self._update_index()

            self._setup_maximum_index_value()

            self._setup_x_axis()

            self._update_text_and_slider()

            self._update_plot()


class ImagesGUI(AbstractSequencerGUI):
    def __init__(self):
        super(ImagesGUI, self).__init__()

        self.capture = None
        self.base_image_name = None
        self.index = None
        self.is_movie_playing = False

        self.image_levels = None
        self.lut = None

        self.flip = None

        self.image_widget = RawImageWidget.RawImageWidget()

        self.image_widget.scaled = True

        self.button_play_movie = QtWidgets.QPushButton()
        self.button_play_movie.resize(100, 20)
        self.button_play_movie.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.button_play_movie.clicked.connect(self.on_play_movie)

        self.button_stop_movie = QtWidgets.QPushButton()
        self.button_stop_movie.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        self.button_stop_movie.resize(100, 20)
        self.button_stop_movie.clicked.connect(self.on_stop_movie)

        self.play_buttons_layout = QtWidgets.QHBoxLayout()
        self.play_buttons_layout.addWidget(self.button_play_movie)
        self.play_buttons_layout.addWidget(self.button_stop_movie)

        self.layout_window.insertWidget(0, self.image_widget)
        self.layout_window.insertLayout(-1, self.play_buttons_layout)

    def _load_data(self):
        try:
            self.base_image = self.repl_globals[self.base_image_name]
        except KeyError:
            print('Variable to plot {} not defined in the REPL'.format(self.base_image_name))
            self.close()

        if self.base_image.__class__ is str:
            try:
                import cv2
                self.capture = cv2.VideoCapture(self.base_image)
            except ModuleNotFoundError:
                print('You need to have Open CV 3 installed to pass a video file to the video sequencer')
                self.close()
        else:
            self.data = self.repl_globals[self.base_image_name]

        if self.superimposed_image_name is not None:
            try:
                self.superimposed_image = self.repl_globals[self.superimposed_image_name]
            except KeyError:
                print('Variable {} to superimpose to plot not defined in the REPL'.format(self.superimposed_image_name))
                self.close()
            if self.superimposed_image.shape[2] != 4:
                print('Superimposed image needs transparency so it needs to be an RGBA (4 values in its 3rd dimension) matrix')
                self.close()

    def _setup_maximum_index_value(self):
        if self.capture is not None:
            frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        elif self.data is not None:
            frames = self.data.shape[0]
        self.max_index = frames - 1
        self.slider_position.setMaximum(self.max_index)

    def _update_plot(self):
        if self.capture is not None:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.index)
            ok, self.data = self.capture.read()
            if ok:
                data = np.transpose(self.data, [1, 0, 2])
            else:
                print('Could not retrieve frame {} from movie'.format(self.index))
        else:
            data = self.data[self.index, :, :].transpose()

        if self.superimposed_image_name is not None:
            superimposed_image = np.transpose(self.superimposed_image, [1, 0, 2])
            #superimposed_image = self.superimposed_image
            if superimposed_image.shape[:2] != data.shape[:2]:
                print('Superimposed image should have the same x, y dimensions as base image')
                self.close()
            visible_pixels_mask = superimposed_image[:, :, 3] > 0
            if len(data.shape) == 3:
                data[visible_pixels_mask] = superimposed_image[visible_pixels_mask, :-1]
            elif len(data.shape) == 2:
                data[visible_pixels_mask] = superimposed_image[visible_pixels_mask, :-2]

        if self.flip == 'ud' or self.flip == 'udlr':
            data = np.fliplr(data)
        if self.flip == 'lr' or self.flip == 'udlr':
            data = np.flipud(data)

        if self.capture is None:
            self.image_widget.setImage(data, levels=self.image_levels, lut=self.lut)
        else:
            self.image_widget.setImage(data)


    def on_timer_tick(self):
        if self.repl_globals is not None:

            if self.data is None:
                self._load_data()

            if self.max_index is None:
                self._setup_maximum_index_value()

            self._update_index()

            self._update_text_and_slider()

            self._update_plot()

            if self.is_movie_playing:
                self.repl_globals[self.tracker_variable_name] += 1

    def on_play_movie(self):
        self.timer.setInterval(1)
        self.is_movie_playing = True

    def on_stop_movie(self):
        self.timer.setInterval(ct.TIMER_UPDATE_TIME_MILLIS)
        self.is_movie_playing = False


if QtWidgets.QApplication.instance() is None:
    app = QtWidgets.QApplication(sys.argv)


def graph_pane(repl_globals, tracker_variable_name, plotted_y_variable_name,
               plotted_x_variable_name=None, transform_name=None):
    win = GraphPaneGUI()
    open_windows[win.uuid] = win
    win.repl_globals = repl_globals
    win.plotted_y_variable_name = plotted_y_variable_name
    win.plotted_x_variable_name = plotted_x_variable_name
    win.tracker_variable_name = tracker_variable_name
    win.transform_name = transform_name
    win.show()


def graph_range(repl_globals, tracker_variable_name, tracker_range_variable_name,
                plotted_y_variable_name, plotted_x_variable_name=None, transform_name=None):
    win = GraphRangeGUI()
    open_windows[win.uuid] = win
    win.repl_globals = repl_globals
    win.plotted_y_variable_name = plotted_y_variable_name
    win.plotted_x_variable_name = plotted_x_variable_name
    win.tracker_variable_name = tracker_variable_name
    win.tracker_range_variable_name = tracker_range_variable_name
    win.transform_name = transform_name
    win.show()


def image_sequence(repl_globals, tracker_variable_name, base_image_name, superimposed_image_name=None,
                   image_levels=None, colormap=None, opacity=None, flip=None):
    win = ImagesGUI()
    open_windows[win.uuid] = win
    win.repl_globals = repl_globals
    win.base_image_name = base_image_name
    win.superimposed_image_name = superimposed_image_name
    win.tracker_variable_name = tracker_variable_name
    win.image_levels = image_levels

    max = 255
    if image_levels is not None:
        max = image_levels[1]

    if colormap is not None:
        if repl_globals[base_image_name].__class__ is str:
            print('Colormap info will not be used on video frames')
        else:
            colormap = plt.get_cmap(colormap)
            colormap._init()
            win.lut = (colormap._lut * max).view(np.ndarray)
    else:
        win.lut = max * np.ones((259, 4))

    if opacity is not None:
        win.lut[:, 3] = opacity
    else:
        win.lut[:, 3] = 255

    win.flip = flip

    win.show()
