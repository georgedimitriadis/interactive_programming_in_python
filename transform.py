

import sys
from PyQt5 import QtWidgets, QtCore, QtGui

import constants as ct


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        # call super class constructor
        super(MainWindow, self).__init__()

        self.repl_globals = None
        self.input_var_name = None
        self.input_variable_value = None
        self.function_name = None
        self.output_var_name = None

        self.is_connection_on = True

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_variable)
        self.timer.start(ct.TIMER_UPDATE_TIME_MILLIS)

        self.resize(300, 100)
        font = QtGui.QFont('Times', pointSize=18, weight=QtGui.QFont.Bold)
        self.setFont(font)

        self.pixmap_green = QtGui.QPixmap('green_dot.png')
        self.pixmap_red = QtGui.QPixmap('red_dot.png')

        layout_window = QtWidgets.QVBoxLayout()
        self.setLayout(layout_window)
        layout_labels = QtWidgets.QHBoxLayout()

        self.label_input = QtWidgets.QLabel()
        self.label_transfrom_func_name = QtWidgets.QLabel()
        self.label_transfrom_func_name.setFont(font)
        self.label_output = QtWidgets.QLabel()

        self.toggle_connection = QtWidgets.QPushButton('Transform')
        self.toggle_connection.setCheckable(True)
        self.toggle_connection.setChecked(True)
        self.toggle_connection.clicked[bool].connect(self.connect)

        layout_labels.addWidget(self.label_input)
        layout_labels.addWidget(self.label_transfrom_func_name)
        layout_labels.addWidget(self.label_output)

        layout_window.addLayout(layout_labels)
        layout_window.addWidget(self.toggle_connection)

    def _get_input_variable(self):
        try:
            self.input_variable_value = self.repl_globals[self.input_var_name]
            self.label_input.setText(str(self.input_variable_value))
        except KeyError:
            print('Variable {} not defined in the REPL'.format(self.input_var_name))
            self.close()

    def _get_function_name(self):
        try:
            self.label_transfrom_func_name.setText('---- {} ---->'.format(str(self.function_name)))
        except KeyError:
            print('Variable {} not defined in the REPL'.format(self.function_name))
            self.close()

    def _set_output_variable(self):
        if self.is_connection_on:
            function = self.repl_globals[self.function_name]
            self.label_transfrom_func_name.setStyleSheet("color: black")
            output_variable_value = eval('function({})'.format(str(self.input_variable_value)))
            try:
                self.repl_globals[self.output_var_name] = output_variable_value
                if output_variable_value.__class__ is bool:
                    if output_variable_value is True:
                        self.label_output.setPixmap(self.pixmap_green)
                    else:
                        self.label_output.setPixmap(self.pixmap_red)
                else:
                    self.label_output.setText(str(output_variable_value))
            except KeyError:
                print('Variable {} not defined in the REPL'.format(self.output_var_name))
                self.close()
        else:
            self.label_transfrom_func_name.setStyleSheet("color: gray")

    def update_variable(self):
        if self.repl_globals is not None:
            self._get_input_variable()

            self._get_function_name()

            self._set_output_variable()

    def connect(self, pressed):
        if pressed:
            self.is_connection_on = True
        else:
            self.is_connection_on = False


if QtWidgets.QApplication.instance() is None:
    app = QtWidgets.QApplication(sys.argv)

windows = []


def connect_repl_var(repl_globals, input_var_name, function_name, output_var_name):
    win = MainWindow()
    windows.append(win)
    win.show()
    win.repl_globals = repl_globals
    win.input_var_name = input_var_name
    win.function_name = function_name
    win.output_var_name = output_var_name
