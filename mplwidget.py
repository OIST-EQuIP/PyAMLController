# Imports
from PyQt5 import QtWidgets
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas, NavigationToolbar2QT as NavigationToolbar
import matplotlib
import seaborn as sn

# Ensure using PyQt5 backend
matplotlib.use('QT5Agg')

# Matplotlib canvas class to create figure
class MplCanvas(Canvas):
    def __init__(self):
        fig = Figure()
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        # Canvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # Canvas.updateGeometry(self)

# Matplotlib widget
class MplWidget(QtWidgets.QWidget):
    sn.set_theme()
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)   # Inherit from QWidget
        self.canvas = MplCanvas()                  # Create canvas object
        self.vbl = QtWidgets.QVBoxLayout()         # Set box for plotting
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.vbl.addWidget(self.toolbar)
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)

    def cla(self):
        self.canvas.axes.cla()

    def set_xlabel(self, time_units):
        self.canvas.axes.set_xlabel('Time (' + time_units + ')')

    def set_ylabel(self, y_quantity, y_units):
        self.canvas.axes.set_ylabel(y_quantity + ' (' + y_units + ')')

    def plot(self, time, data):
        self.canvas.axes.plot(time, data)

    def set_yscale_log(self):
        self.canvas.axes.set_yscale('log')

    def draw(self):
        self.canvas.draw()

