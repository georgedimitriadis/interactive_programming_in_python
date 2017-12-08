# -*- coding: utf-8 -*-


import re
import threading
import matplotlib.pyplot as plt

def parsescript(fname, axes, scope):
    ui = []
    with open(fname) as f:
        for init, result in re.findall('#@(.*?)\n(.*?)#@', f.read(), re.S):
            args = init.split(' ')
            c = connectcode(result)
            if args[0] == 'button':
                b = plt.Button(axes, args[1])
                b.on_clicked(c)
            elif args[0] == 'slider':
                b = plt.Slider(axes, args[1], 0, 10)
                bind = connectslider(args[2], scope)
                b.on_changed(bind)
                b.on_changed(c)
                timer = connecttimer(b, args[2], scope)
                timer()
            ui.append(b)
    return ui


def connectcode(code):
    codeobj = compile(code, 'callbacks', 'exec')

    def connection(x):
        exec(codeobj) in globals()
    return connection


def connectslider(name, scope):
    def connection(x):
        if name in scope.keys():
            scope[name] = x
    return connection


def connecttimer(slider, name, scope):
    def connection():
        threading.Timer(0.1, connection).start()
        current = scope[name]
        if slider.val != current:
            slider.set_val(current)
    return connection



'''
Example UI:

#@slider param1 x
print x
#@

'''