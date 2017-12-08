

import magicui

import matplotlib.pyplot as plt

filename = r'E:\George\SourceCode\Repos\interactive_programming_in_python\test.py'


fig = plt.figure(0)
ax = fig.add_axes([0.1, 0.1, 0.9, 0.9])



x = 5
gl = globals()

magicui.parsescript(filename, ax, gl)
#@slider param1 x
print(x)
#@
