
from PyQt5 import QtWidgets

import basic_transform as bt


class MainWindow(bt.BasicTransform):
    def __init__(self, repl_globals, input_var_name, function_name, output_var_name, function_args_name=None):
        # call super class constructor
        super(MainWindow, self).__init__(repl_globals, input_var_name, function_name, output_var_name, function_args_name)

        self.input_widget = QtWidgets.QComboBox()
        try:
            drop_down_variable = self.repl_globals[self.input_var_name]
        except KeyError:
            print('Variable {} not defined in the REPL'.format(self.input_var_name))
            self.close()
        for item in drop_down_variable:
            self.input_widget.addItem(str(item), item)
        self.input_widget.setCurrentIndex(0)

        self.layout_labels.addWidget(self.input_widget)
        self.layout_labels.addWidget(self.label_transfrom_func_name)
        self.layout_labels.addWidget(self.label_output)

    def _get_input_var_value(self):
        index = self.input_widget.currentIndex()
        self.input_var_value = self.input_widget.itemData(index)


def connect_repl_var(repl_globals, input_var_name, function_name, output_var_name, function_args_name=None):
    win = MainWindow(repl_globals, input_var_name, function_name, output_var_name, function_args_name)
    bt.open_windows[win.uuid] = win
    win.show()


