
from PyQt5 import QtWidgets, QtCore

import basic_transform as bt


class MainWindow(bt.BasicTransform):
    def __init__(self, repl_globals, input_var_name, function_name, output_var_name, function_args_name=None,
                 slider_limits=None):
        # call super class constructor
        super(MainWindow, self).__init__(repl_globals, input_var_name, function_name, output_var_name,
                                         function_args_name)

        self.update_input_from_repl = True

        self.input_widget = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        if slider_limits is not None:
            self.input_widget.setRange(slider_limits[0], slider_limits[1])
        self.input_widget.valueChanged.connect(self._on_slider_value_changed)

        self.input_label = QtWidgets.QLabel()

        self.layout_labels.addWidget(self.input_label)
        self.layout_labels.addWidget(self.label_transfrom_func_name)
        self.layout_labels.addWidget(self.label_output)
        self.layout_window.addWidget(self.input_widget)

    def _set_input_label(self):
        try:
            length = len(self.input_var_value)
        except:
            length = 0
        try:
            if length > 5:
                self.input_label.setText(str(self.input_var_name))
            else:
                self.input_label.setText('{} = {}'.format(self.input_var_name, str(self.input_var_value)))
        except:
            pass

    def _on_slider_value_changed(self):
        self.input_var_value = self.input_widget.value()
        self.repl_globals[self.input_var_name] = self.input_var_value
        self._set_input_label()

    def _get_input_var_value(self):
        if self.update_input_from_repl:
            try:
                self.input_var_value = self.repl_globals[self.input_var_name]
                self.input_widget.setValue(self.input_var_value)
                self._set_input_label()
            except KeyError:
                print('Variable {} not defined in the REPL'.format(self.input_var_name))
                self.close()


def connect_repl_var(repl_globals, input_var_name, function_name, output_var_name, function_args_name=None,
                     slider_limits=None):
    win = MainWindow(repl_globals, input_var_name, function_name, output_var_name, function_args_name,
                     slider_limits)
    bt.open_windows[win.uuid] = win
    win.show()
