
import sys
from PyQt5 import QtWidgets, QtCore, QtGui

import numpy as np
import pyqtgraph as pg
pg.setConfigOption('background', (200, 0, 0, 50))
pg.setConfigOption('foreground', (0, 0, 200, 255))
from pyqtgraph.widgets import RawImageWidget

import matplotlib.pyplot as plt

import uuid

import image_superposition as ims

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
        self.fillLevel = None
        self.brush = (255, 255, 255, 255)

        self.plot_widget = pg.PlotWidget()
        self.plot_data_item = pg.PlotDataItem()
        self.plot_data_item.setPen((0, 0, 0, 255))
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
            if len(self.data.shape) == 1:
                if len(self.data) == len(self.x_axis):
                    self.stepmode = False
                    self.fillLevel = None
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
                if self.data.shape[-1] == len(self.x_axis):
                    # Tile so that the x_axis corresponds to data[index, :, :].flatten()
                    # example: t = [0,1,2,3] for data.shape=(i, 2, 4) becomes t = [0, 1, 2, 3, 0, 1, 2, 3, 4]
                    self.x_axis = np.tile(self.x_axis, self.data.shape[0])
                else:
                    print('X axis length {} needs to be equal (or one larger for a histogram) to data length {}' \
                          .format(self.x_axis.shape[0], self.data.shape[-1]))
                    self.close()

    def _update_plot(self):
        if len(np.shape(self.data)) == 1:
            if self.fillLevel is None:
                self.plot_data_item.setData(self.x_axis, self.data, stepMode=self.stepmode, brush=self.brush)
            else:
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
    def __init__(self, num_of_images=1):
        super(ImageGUI, self).__init__()

        self.num_of_images = num_of_images
        self.data = None

        self.image_levels_name = None
        self.colormaps_name = None
        self.opacities_name = None
        self.flips_name = None

        self.image_widget = ims.StackedRawImageWidget(self.num_of_images)
        self.image_widget.scaled = True

        self.layout_window.insertWidget(0, self.image_widget.base_image())



    def _load_data(self):
        try:
            self.data = self.repl_globals[self.plotted_y_variable_name]
        except KeyError:
            print('Variable to plot {} not defined in the REPL'.format(self.plotted_y_variable_name))
            self.close()

    def _update_image_levels(self):
        self.image_levels = None
        if self.image_levels_name is not None:
            try:
                self.image_levels = self.repl_globals[self.image_levels_name]
            except KeyError:
                print('Variable of image_levels {} not defined in the REPL'.format(self.image_levels_name))
                self.close()
            if self.num_of_images > 1:
                assert np.array(self.image_levels).shape[0] == self.num_of_images, 'The number of tuples or Nones in ' \
                                                                                   'the image_levels is not the same ' \
                                                                                   'as the number of images'
            else:
                assert len(self.image_levels) == 2, 'The image_levels for one image needs to be a tuple with two numbers'

    def _update_colormaps(self):
        self.colormaps = None
        if self.colormaps_name is not None:
            try:
                self.colormaps = self.repl_globals[self.colormaps_name]
            except KeyError:
                print('Variable of colormaps {} not defined in the REPL'.format(self.colormaps_name))
                self.close()
            if self.num_of_images > 1:
                assert np.array(self.colormaps).shape[0] == self.num_of_images, 'The number of strings or Nones in the'\
                                                                                'colormaps is not the same as the' \
                                                                                'number of images'
            else:
                assert self.colormaps.__class__ is str, 'The colormap for one image needs to be a string'

    def _update_opacities(self):
        self.opacities = None
        if self.opacities_name is not None:
            try:
                self.opacities = self.repl_globals[self.opacities_name]
            except KeyError:
                print('Variable of opacities {} not defined in the REPL'.format(self.opacities_name))
                self.close()
            if self.num_of_images > 1:
                assert np.array(self.opacities).shape[0] == self.num_of_images, 'The number of values or Nones in the' \
                                                                                'opacities is not the same as the' \
                                                                                'number of images'

    def _update_flips(self):
        self.flips = None
        if self.flips_name is not None:
            try:
                self.flips = self.repl_globals[self.flips_name]
            except KeyError:
                print('Variable of flips {} not defined in the REPL'.format(self.flips_name))
                self.close()
            if self.num_of_images > 1:
                assert np.array(self.flips).shape[0] == self.num_of_images, 'The number of strings or Nones in the' \
                                                                            'flips is not the same as the' \
                                                                            'number of images'

    def _do_flip(self, data, flip):
        if flip == 'ud' or flip == 'udlr':
            data = np.fliplr(data)
        if flip == 'lr' or flip == 'udlr':
            data = np.flipud(data)

        return data

    def _update_plot(self):

        if self.num_of_images == 1:
            data = self.data
            if len(data.shape) == 2:
                data = np.transpose(data)
            elif len(data.shape) == 3:
                data = np.transpose(data, [1, 0, 2])
            if self.flips is not None:
                data = self._do_flip(data, self.flips)

        else:
            data = list(self.data).copy()
            for f in np.arange(self.num_of_images):
                if len(data[f].shape) == 2:
                    data[f] = np.transpose(data[f])
                    if self.flips is not None:
                        data[f] = self._do_flip(data[f], self.flips)
                elif len(data[f].shape) == 3:
                    data[f] = np.transpose(data[f], [1, 0, 2])

                if self.flips is not None:
                    if self.flips[f] is not None:
                        data[f] = self._do_flip(data[f], self.flips[f])

        self.image_widget.assign_data(data)

    def on_timer_tick(self):
        if self.repl_globals is not None:

            self._load_data()

            self._update_image_levels()
            self._update_colormaps()
            self._update_opacities()
            self._update_flips()
            self.image_widget.generate_luts(self.image_levels, self.colormaps, self.opacities)

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
          image_levels_name=None, colormaps_name=None, opacities_name=None, flips_name=None,
          number_of_images=1):

    win = ImageGUI(num_of_images=number_of_images)
    open_windows[win.uuid] = win
    win.repl_globals = repl_globals
    win.plotted_y_variable_name = plotted_y_variable_name
    win.image_levels_name = image_levels_name
    win.colormaps_name = colormaps_name
    win.opacities_name = opacities_name
    win.flips_name = flips_name

    win.show()

