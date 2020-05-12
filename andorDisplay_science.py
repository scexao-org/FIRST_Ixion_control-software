################################################################################
##################          ANDOR iXon Live Viewer          ####################
################################################################################

import numpy as np
from threading import Thread


from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
else:
    from matplotlib.backends.backend_qt4agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure


################################################################################
##################             Plot application             ####################
################################################################################


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        dynamic_canvas = FigureCanvas(Figure(figsize=(8, 5)))
        layout.addWidget(dynamic_canvas)
        #self.addToolBar(QtCore.Qt.BottomToolBarArea, NavigationToolbar(dynamic_canvas, self))

        self._dynamic_ax = dynamic_canvas.figure.subplots()
        self._timer = dynamic_canvas.new_timer(1, [(self._update_canvas, (), {})])
        self._timer.start()

        self.data = []
        self.data_new = []
        self.andor_ctrl = None

    def _update_canvas(self):
        self.data_new = self.andor_ctrl.update()
        if self.data_new is not None:
            self.data = self.data_new
            self._dynamic_ax.clear()
            self._dynamic_ax.imshow(self.data, origin='lower')
            self._dynamic_ax.figure.canvas.draw()
        else:
            self.pub.pprint("data is None")
            self._dynamic_ax.clear()
            self._dynamic_ax.imshow(self.data, origin='lower')
            self._dynamic_ax.figure.canvas.draw()

    def set_andorCtrl(self, Andor_Ctrl):
        '''
        This method lets the plot application know what is the Andor control application.
        It's needed to recover the camera data from it, via its update() method.
        '''
        self.andor_ctrl = Andor_Ctrl

    def set_publisher(self, publisher):
        '''
        This method install the communication in the object.
        It's needed to print every messages.
        '''
        self.pub = publisher