
import sys
import os

from PyQt5 import QtWidgets, QtCore, QtGui

import constants as ct

import uuid

open_windows = {}


class BasicTransform(QtWidgets.QWidget):
    def __init__(self, repl_globals, input_var_name, function_name, output_var_name, function_args_name=None):
        # call super class constructor
        super(BasicTransform, self).__init__()

        self.uuid = uuid.uuid4()

        self.input_var_value = None  # Needs to be implemented
        self.input_widget = None  # Needs to be implemented

        self.repl_globals = repl_globals
        self.input_var_name = input_var_name
        self.function_name = function_name
        self.function_args_name = function_args_name
        self.output_var_name = output_var_name

        self.is_connection_on = True

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_variable)
        self.timer.start(ct.TIMER_UPDATE_TIME_MILLIS)

        self.resize(300, 100)
        font = QtGui.QFont('Times', pointSize=18, weight=QtGui.QFont.Bold)
        self.setFont(font)

        current_path = os.path.dirname(os.path.realpath(__file__))
        self.pixmap_green = QtGui.QPixmap(os.path.join(current_path, 'resources', 'green_dot.png'))
        self.pixmap_red = QtGui.QPixmap(os.path.join(current_path, 'resources', 'red_dot.png'))

        self.layout_window = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout_window)
        self.layout_labels = QtWidgets.QHBoxLayout()

        self.label_transfrom_func_name = QtWidgets.QLabel()
        self.label_transfrom_func_name.setFont(font)
        self.label_transfrom_func_name.setStyleSheet("color: black")
        if self.function_name is None:
            self.label_transfrom_func_name.setText('-------->')
        else:
            self.label_transfrom_func_name.setText('---- {} ---->'.format(str(self.function_name)))
        self.label_output = QtWidgets.QLabel()

        self.toggle_connection = QtWidgets.QPushButton('Transform')
        self.toggle_connection.setBaseSize(50, 20)
        self.toggle_connection.setCheckable(True)
        self.toggle_connection.setChecked(True)
        self.toggle_connection.clicked[bool].connect(self.connect)

        self.layout_window.addLayout(self.layout_labels)
        self.layout_window.addWidget(self.toggle_connection)

    def closeEvent(self, event):
        del open_windows[self.uuid]
        self.close()
        event.accept()

    # Needs to be implemented
    def _get_input_var_value(self):
        pass

    def _set_input_var_name(self):
        try:
            length = len(self.input_var_value)
        except:
            length = 0
        try:
            if length > 5:
                self.input_widget.setText(str(self.input_var_name))
            else:
                self.input_widget.setText('{} = {}'.format(self.input_var_name, str(self.input_var_value)))
        except:
            pass

    def _set_function_name(self):
        try:
            self.label_transfrom_func_name.setText('{}({}) = '.format(str(self.function_name), str(self.input_var_name)))
        except KeyError:
            print('Variable {} not defined in the REPL'.format(self.function_name))
            self.close()

    def _get_currently_used_function(self):
        if self.function_name is not None:
            try:
                function = self.repl_globals[self.function_name]
            except KeyError:
                print('Variable {} not defined in the REPL'.format(self.function_name))
                self.close()
        else:
            function = None

        return function

    def _get_params_name(self):
        try:
            self.function_args_value = self.repl_globals[self.function_args_name]
            try:
                len(self.function_args_value)
            except TypeError:
                self.function_args_value = [self.function_args_value]
        except KeyError:
            print('Variable {} not defined in the REPL'.format(self.function_args_name))
            self.close()

    def _calculate_output(self):

        function = self._get_currently_used_function()

        if self.function_args_name is not None:
            output_variable_value = function(self.input_var_value, *self.function_args_value)
        else:
            output_variable_value = function(self.input_var_value)

        return output_variable_value

    def _set_output_variable(self):
        if self.is_connection_on:

            output_variable_value = self._calculate_output()

            try:
                self.repl_globals[self.output_var_name] = output_variable_value
            except KeyError:
                print('Variable {} not defined in the REPL'.format(self.output_var_name))
                self.close()
            try:
                if output_variable_value.__class__ is bool:
                    if output_variable_value is True:
                        self.label_output.setPixmap(self.pixmap_green)
                    else:
                        self.label_output.setPixmap(self.pixmap_red)
                elif output_variable_value.__class__ is int or \
                        output_variable_value.__class__ is float or \
                        output_variable_value.__class__ is str:
                    self.label_output.setText(str(output_variable_value))
                else:
                    self.label_output.setText(str(self.output_var_name))
            except:
                pass

            self.label_transfrom_func_name.setStyleSheet("color: black")
        else:
            self.label_transfrom_func_name.setStyleSheet("color: gray")

    def update_variable(self):
        if self.repl_globals is not None:
            self._get_input_var_value()

            self._set_input_var_name()

            self._set_function_name()

            if self.function_args_name is not None:
                self._get_params_name()

            self._set_output_variable()

    def connect(self, pressed):
        if pressed:
            self.is_connection_on = True
        else:
            self.is_connection_on = False


if QtWidgets.QApplication.instance() is None:
    app = QtWidgets.QApplication(sys.argv)

windows = []
