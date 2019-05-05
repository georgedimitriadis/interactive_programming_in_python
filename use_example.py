
import numpy as np


import sequence_viewer
import transform
import drop_down
import one_shot_viewer
import video_viewer


# Make some data
data1 = np.random.random((10, 10000))
for i in range(10):
    data1[i] += i

data2 = np.random.random(500)

# Have a look at them
position1 = 0
range1 = 1000
sequence_viewer.graph_range(globals(), 'position1', 'range1', 'data1')

position2 = 0
range2 = 10
sequence_viewer.graph_range(globals(), 'position2', 'range2', 'data2')

# Also you can view data in panes
pane = 0
sequence_viewer.graph_pane(globals(), 'pane', 'data1')
# The pane viewer shows te last one or two dimensions of a 2d or 3d data set and itterates over the first one.


# Connect two guis
def pos1_to_pos2(pos1):
    if pos1 >= 0 and pos1 <= 4000:
        return int(pos1 / 10)
    elif pos1 < 0:
        return 0
    elif pos1 > 4000:
        return 400


transform.connect_repl_var(globals(), 'position1', 'pos1_to_pos2', 'position2')
# Press the Transform to deactivate the function from running and so stop the connection
# If the function passed to the transform returns bool then you get nice red/green leds for False and True


# SOME NOTES
# The variables in the command line are always connected to the guis. After you change them in the guys look for their
# values in the repl.
# Change the different values of the variables in the repl to see the guis update.


# The other guis available at the moment are
# 1) One more types of sequence_viewer for images or frames of video (you can pass the name of a video in the
# image_sequence function, or a 2d numpy array).
# 2) The two types of one_shot_viewers (graph and image) where the shown data gets updated by the repl and not by the gui
# 3) The video_viewer where a video can be played at real time (but only gives out frame keys and not individual frames)
# 4) The drop_down transform that is like the transform but has a drop down as input (connects to an itterable)

# If in the graph function of the one_shot_viewer you pass x data that are one element longer than the y data then you
# get a histogram (it assumes the x data are the edges as given by the np.histogram function)

# THERE ARE STILL PLENTY OF BUGS THAT NEED SQUASHING
