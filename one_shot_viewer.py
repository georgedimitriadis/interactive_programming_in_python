
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


class AbstractOneShotGUI(QtWidgets.QWidget):
    def __init__(self):
        # call super class constructor
        super(AbstractOneShotGUI, self).__init__()

        self.uuid = uuid.uuid4()
        self.repl_globals = None
        self.plotted_y_variable_name = None
        self.plotted_x_variable_name = None
        self.x_axis = None

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start(ct.TIMER_UPDATE_TIME_MILLIS)

        self.layout_window = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout_window)

        self.resize(800, 600)

    def closeEvent(self, event):
        del open_windows[self.uuid]
        self.close()
        event.accept()

    def on_timer_tick(self):
        pass


class GraphGUI(AbstractOneShotGUI):
    def __init__(self):
        super(GraphGUI, self).__init__()

        self.data = None
        self.stepmode = False
        self.fillLevel = 0
        self.brush = (255, 255, 255, 255)

        self.plot_widget = pg.PlotWidget()
        self.plot_data_item = pg.PlotDataItem()
        self.plot_widget.addItem(self.plot_data_item)

        self.layout_window.insertWidget(0, self.plot_widget)

    def _load_data(self):
        try:
            self.data = np.array(self.repl_globals[self.plotted_y_variable_name])
        except KeyError:
            print('Y axis variable to plot {} not defined in the REPL'.format(self.plotted_y_variable_name))
            self.close()

    def _setup_x_axis(self):
        if self.plotted_x_variable_name is None:
            if len(self.data.shape) == 1:
                self.x_axis = np.arange(self.data.shape[0])
            if len(self.data.shape) == 2:
                self.x_axis = np.tile(np.arange(self.data.shape[1]), self.data.shape[0])
        else:
            try:
                self.x_axis = np.array(self.repl_globals[self.plotted_x_variable_name])
            except KeyError:
                print('X axis variable to plot {} not defined in the REPL'.format(
                    self.plotted_x_variable_name))
                self.close()
            if len(self.data) == len(self.x_axis):
                self.stepmode = False
                self.fillLevel = 0
                self.brush = (255, 255, 255, 255)
            elif len(self.data) + 1 == len(self.x_axis): # If the x axis is one larger than the y then draw a histogram
                self.stepmode = True
                self.fillLevel = 0
                self.brush = (0, 0, 255, 150)
            else:
                print('X axis length {} needs to be equal (or one larger for a histogram) to data length {}'\
                      .format(self.x_axis.shape[0], self.data.shape[-1]))
                self.close()

            if len(self.data.shape) == 2:
                # Tile so that the x_axis corresponds to data[index, :, :].flatten()
                # example: t = [0,1,2,3] for data.shape=(i, 2, 4) becomes t = [0, 1, 2, 3, 0, 1, 2, 3, 4]
                self.x_axis = np.tile(self.x_axis, self.data.shape[0])

    def _update_plot(self):
        if len(np.shape(self.data)) == 1:
            self.plot_data_item.setData(self.x_axis, self.data, stepMode=self.stepmode,
                                        fillLevel=self.fillLevel, brush=self.brush)
        elif len(np.shape(self.data)) == 2:
            # The connect argument allows a single line to be broken up (see pg.ArrayToQPath) so that the
            # 1D array data[index, :, :].flatten() shows up as multiple independent lines
            connect = np.ones(len(self.x_axis))
            connect[np.arange(self.data.shape[1] - 1, self.data.shape[1] * self.data.shape[0], self.data.shape[1])] = 0
            self.plot_data_item.opts['connect'] = connect

            y = self.data.flatten()
            self.plot_data_item.setData(x=self.x_axis, y=y)

    def on_timer_tick(self):
        if self.repl_globals is not None:

            self._load_data()

            if self.x_axis is None:
                self._setup_x_axis()

            self._update_plot()


class ImageGUI(AbstractOneShotGUI):
    def __init__(self):
        super(ImageGUI, self).__init__()

        self.data = None

        self.image_levels = None
        self.lut = None

        self.flip = None

        self.image_widget = RawImageWidget.RawImageWidget()
        self.image_widget.scaled = True

        self.layout_window.insertWidget(0, self.image_widget)

    def _load_data(self):
        try:
            self.data = self.repl_globals[self.plotted_y_variable_name]
        except KeyError:
            print('Variable to plot {} not defined in the REPL'.format(self.plotted_y_variable_name))
            self.close()

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

        if self.flip == 'ud' or self.flip == 'udlr':
            data = np.fliplr(data)
        if self.flip == 'lr' or self.flip == 'udlr':
            data = np.flipud(data)

        self.image_widget.setImage(data, levels=self.image_levels, lut=self.lut)

    def on_timer_tick(self):
        if self.repl_globals is not None:

            self._load_data()

            self._update_plot()


if QtWidgets.QApplication.instance() is None:
    app = QtWidgets.QApplication(sys.argv)


def graph(repl_globals, plotted_y_variable_name, plotted_x_variable_name=None):
    win = GraphGUI()
    open_windows[win.uuid] = win
    win.repl_globals = repl_globals
    win.plotted_y_variable_name = plotted_y_variable_name
    win.plotted_x_variable_name = plotted_x_variable_name
    win.show()


def image(repl_globals, plotted_y_variable_name,
                   image_levels=None, colormap=None, flip=None):
    win = ImageGUI()
    open_windows[win.uuid] = win
    win.repl_globals = repl_globals
    win.plotted_y_variable_name = plotted_y_variable_name
    win.image_levels = image_levels

    max = 255
    if image_levels is not None:
        max = image_levels[1]

    if colormap is not None:
        if repl_globals[plotted_y_variable_name].__class__ is str:
            print('Colormap info will not be used on video frames')
        else:
            colormap = plt.get_cmap(colormap)
            colormap._init()
            win.lut = (colormap._lut * max).view(np.ndarray)

    win.flip = flip

    win.show()