import GUI
import Simulation
import sys
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np
import os
import time
from Sensor import Sensor
from SensorData import SensorData


class ApplicationHandler:
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)
        self.MainWindow = QtWidgets.QMainWindow()
        self.filename = ""
        self.ui = GUI.Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)
        self.ui.actionOpen_mesh.triggered.connect(self.open_msh)
        self.ui.actionCreate_mesh.triggered.connect(self.open_stl)
        self.ui.pushButton.clicked.connect(self.run)
        self.MainWindow.show()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_graphs)
        self.lines = []
        self.freq = 100
        self.start = 0
        self.rampup = 5
        self.stimdur = 10
        self.rampdown = 5
        self.pause = 10
        self.repeats = 5
        self.mutex = QtCore.QMutex()
        self.threadpool = QtCore.QThreadPool()
        self.data = SensorData()
        self.xdata = []
        self.ydata = []
        self.sensors = []

        test = self.ui.graphicsView
        test.setBackground((0, 0, 0, 0))
        sys.exit(app.exec_())

    def open_msh(self):
        self.filename, _ = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow, "QtWidgets.QFileDialog.getOpenFileName()")
        file = os.path.basename(self.filename)
        self.ui.progressBar.setProperty("value", 100)
        if file == "":
            self.ui.label_9.setText("No model selected")
        else:
            self.ui.label_9.setText("Selected: " + file)

    def open_stl(self):
        self.filename, _ = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow, "QtWidgets.QFileDialog.getOpenFileName()")
        # TODO
        # import gmsh_api.gmsh as gmsh
        # filename = 'model'
        #
        # if not os.path.isfile('models/nonMRI/{0}/{0}.msh'.format(filename)):
        #     print("{0}.msh file does not exist yet, creating one from .stl files".format(filename))
        #     gmsh.initialize()
        #     current = 1
        #     if not os.path.isfile('models/nonMRI/{0}/{0}Scalp.stl'.format(filename)):
        #         raise FileNotFoundError("Scalp stl file does not exist")
        #     gmsh.merge('models/nonMRI/{0}/{0}Scalp.stl'.format(filename))
        #     gmsh.model.geo.addSurfaceLoop([current], 5)
        #
        #     print("Added Scalp information")
        #     current = current + 1
        #     if os.path.isfile('models/nonMRI/{0}/{0}Skull.stl'.format(filename)):
        #         gmsh.merge('models/nonMRI/{0}/{0}Skull.stl'.format(filename))
        #         gmsh.model.geo.addSurfaceLoop([current], 4)
        #         gmsh.model.geo.addVolume([4], 4)
        #         print("Added Skull information")
        #         current = current + 1
        #     if os.path.isfile('models/nonMRI/{0}/{0}Brain.stl'.format(filename)):
        #         gmsh.merge('models/nonMRI/{0}/{0}Brain.stl'.format(filename))
        #         gmsh.model.geo.addSurfaceLoop([current], 2)
        #
        #         print("Added Brain information")
        #
        #     gmsh.model.geo.addVolume([5, 2], 5)
        #     gmsh.model.geo.addVolume([2], 2)
        #     gmsh.model.geo.synchronize()
        #     print("Generating mesh...")
        #     gmsh.model.mesh.generate(3)
        #     print("Writing mesh")
        #     gmsh.write('models/nonMRI/{0}/{0}.msh'.format(filename))
        #     gmsh.finalize()
        #     print("Successfully created {0}.msh".format(filename))

    def run(self):
        if self.filename == "" and False:
            print("No model selected!")
        else:
            if self.filename == "":
                self.filename = "/home/leroy/Thesis/Code/models/nonMRI/model/model.msh"
            currents = []
            for x in range(3):
                currents.append(float(self.ui.tableWidget.item(x, 0).text())/1000)
            # file = simulation.run(self.filename, currents)
            # peak = np.array(simulation.analyse(file))

            peak = np.array([0.1, 0.2, 0.3])

            self.rampup = 5
            self.stimdur = 10
            self.rampdown = 5
            self.pause = 10
            self.repeats = 5
            self.freq = 10

            x = np.arange(0, 5*(5+10+5+10), 1.0/self.freq)
            y = np.zeros([len(peak), len(x)])

            for i, timestep in enumerate(x):
                timestep %= self.rampup+self.stimdur+self.rampdown+self.pause
                if timestep < self.rampup:
                    y[:, i] = peak * timestep / self.repeats
                elif self.rampup+self.stimdur < timestep < self.rampup+self.stimdur+self.rampdown:
                    y[:, i] = peak * (1 - (timestep - self.rampup - self.stimdur) / self.repeats)
                elif timestep >= self.rampup + self.stimdur + self.rampdown:
                    y[:, i] = 0
                else:
                    y[:, i] = peak

            test = self.ui.graphicsView
            for i in range(len(peak)):
                plott = test.addPlot(row=i, col=0)
                plott.plot(x=x, y=y[i], pen=pg.mkPen(0.6, width=2), antialias=True)
                plott.plot(x=x[0:1], y=y[i, 0:1], pen=pg.mkPen(color='r', width=2), antialias=True)
                plott.setClipToView(True)
                if i == 0:
                    plott.getViewBox().register("test")
                else:
                    plott.getViewBox().linkView(pg.ViewBox.XAxis, "test")
                plott.getViewBox().setMouseEnabled(y=False)
                plott.getViewBox().setLimits(xMin=0, xMax=x[-1])
                plott.getViewBox().setRange(yRange=(-.05, 0.35))
                plott.showGrid(y=True, alpha=0.9)
                self.lines.append(plott.addLine(x=0, pen=pg.mkPen(color=(255, 0, 0))))

            self.start = time.time()
            for i in range(3):
                self.sensors.append(Sensor(SensorData(), self.start))
                self.threadpool.start(self.sensors[i])
                self.xdata.append([])
                self.ydata.append([])
            self.timer.start(10)

    def update_graphs(self):
        test = self.ui.graphicsView
        curtime = time.time() - self.start

        for i in range(3):
            newData = self.sensors[i].data.getData()

            if newData is not None:
                plt = test.getItem(i, 0)

                self.xdata[i].extend(newData[0])
                self.ydata[i].extend(newData[1])
                plt.listDataItems()[1].setData(x=self.xdata[i], y=self.ydata[i])
            self.lines[i].setValue(curtime)


if __name__ == "__main__":
    ApplicationHandler()
