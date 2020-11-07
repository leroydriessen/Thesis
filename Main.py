import os
import sys
import time

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore

from GUI import Ui_MainWindow
from Sensor import Sensor
from SensorData import SensorData
from Simulation import Simulation


class ApplicationHandler:
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)
        self.MainWindow = QtWidgets.QMainWindow()
        self.filename = ""
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)
        self.ui.actionOpen_mesh.triggered.connect(self.open_msh)
        self.ui.actionCreate_mesh.triggered.connect(self.open_stl)
        self.ui.pushButton.clicked.connect(self.run)
        self.MainWindow.show()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_graphs)
        self.lines = []
        self.freq = 100
        self.start_time = 0
        self.end_time = 0
        self.ramp_up = 5
        self.duration = 10
        self.ramp_down = 5
        self.pause = 10
        self.repeats = 5
        self.thread_pool = QtCore.QThreadPool()
        self.thread_pool.setExpiryTimeout(5)
        self.x_data = []
        self.y_data = []
        self.sensors = []
        self.full = True
        self.running = False
        self.electrodes = [[30, 55, -10], [-20, 20, 20], [30, 30, 30]]

        test = self.ui.graphicsView
        test.setBackground((0, 0, 0, 0))
        code = app.exec_()
        for sensor in self.sensors:
            sensor.cancel()
        self.thread_pool.waitForDone()
        sys.exit(code)

    def open_msh(self):
        self.filename, _ = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow, "QtWidgets.QFileDialog.getOpenFileName()")
        file = os.path.basename(self.filename)
        self.ui.progressBar.setProperty("value", 100)
        if file == "":
            self.ui.modelSelection.setText("No model selected")
        else:
            self.ui.modelSelection.setText("Selected: " + file)

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

    def end_experiment(self):
        self.thread_pool.waitForDone()
        self.running = False
        self.timer.stop()
        self.sensors = []
        self.ui.pushButton.setText("Run")

    def restart(self):
        self.running = False
        self.timer.stop()
        self.x_data = []
        self.y_data = []
        for sensor in self.sensors:
            sensor.cancel()
        self.sensors = []
        self.thread_pool.waitForDone()
        self.ui.graphicsView.clear()
        self.ui.pushButton.setText("Run")
        self.lines = []

    def run(self):
        if self.running:
            self.restart()
        else:
            if self.filename == "" and not self.full:
                print("No model selected!")
            else:
                if self.filename == "":
                    self.filename = "/home/leroy/Thesis/Code/models/nonMRI/sphere_models/sphere100.msh"

                self.restart()

                self.running = True
                self.ui.pushButton.setDisabled(True)
                self.ui.pushButton.setCheckable(True)
                self.ui.pushButton.setChecked(True)
                self.ui.pushButton.setText("Stop")
                currents = []
                for x in range(3):
                    currents.append(float(self.ui.electrodeTable.item(x, 0).text())/1000)
                if self.full:
                    simulation = Simulation(self.filename, currents, self.electrodes)
                    simulation.communication.peak.connect(self.experiment)
                    self.thread_pool.start(simulation)
                else:
                    self.experiment(np.array([0.1, 0.2, 0.3]))

    def experiment(self, peak):
        self.ui.pushButton.setDisabled(False)
        self.ui.pushButton.setCheckable(False)

        self.ramp_up = float(self.ui.rampup.text())
        self.duration = float(self.ui.stimdur.text())
        self.ramp_down = float(self.ui.rampdown.text())
        self.pause = float(self.ui.pause.text())
        self.repeats = int(self.ui.repeats.text())
        self.freq = 10

        sequence_time = self.ramp_up + self.duration + self.ramp_down + self.pause
        x = np.arange(0, self.repeats * sequence_time, 1.0 / self.freq)
        y = np.zeros([len(peak), len(x)])

        for i, timestamp in enumerate(x):
            timestamp %= self.ramp_up + self.duration + self.ramp_down + self.pause
            if timestamp < self.ramp_up:
                y[:, i] = peak * timestamp / self.ramp_up
            elif self.ramp_up+self.duration < timestamp < self.ramp_up+self.duration+self.ramp_down:
                y[:, i] = peak * (1 - (timestamp - self.ramp_up - self.duration) / self.ramp_down)
            elif timestamp >= self.ramp_up + self.duration + self.ramp_down:
                y[:, i] = 0
            else:
                y[:, i] = peak

        y_min = max(max(v) for v in y)
        y_max = min(min(v) for v in y)
        y_range = y_max-y_min
        margin = 0.2*y_range

        for i in range(len(peak)):
            plot_item = self.ui.graphicsView.addPlot(row=i, col=0)
            plot_item.plot(x=x, y=y[i], pen=pg.mkPen(0.6, width=2), antialias=True)
            plot_item.plot(x=x[0:1], y=y[i, 0:1], pen=pg.mkPen(color='r', width=2), antialias=True)
            plot_item.setClipToView(True)
            plot_item.showGrid(y=True, alpha=0.9)

            view_box = plot_item.getViewBox()
            if i == 0:
                view_box.register("main")
            else:
                view_box.linkView(pg.ViewBox.XAxis, "main")
            view_box.setMouseEnabled(y=False)
            view_box.setLimits(xMin=0, xMax=x[-1])
            view_box.setRange(yRange=(y_min-margin, y_max+margin))

            self.lines.append(plot_item.addLine(x=0, pen=pg.mkPen(color=(255, 0, 0))))

        self.start_time = time.time()
        self.end_time = self.repeats*sequence_time

        for i in range(3):
            self.sensors.append(Sensor(SensorData(), self.start_time, self.end_time))
            self.thread_pool.start(self.sensors[i])
            self.x_data.append([])
            self.y_data.append([])
        self.timer.start(10)

    def update_graphs(self):
        test = self.ui.graphicsView
        timestamp = time.time() - self.start_time

        if timestamp > self.end_time:
            self.end_experiment()
            return

        for i in range(3):
            new_data = self.sensors[i].data.getData()

            if new_data is not None:
                plt = test.getItem(i, 0)
                self.x_data[i].extend(new_data[0])
                self.y_data[i].extend(new_data[1])
                plt.listDataItems()[1].setData(x=self.x_data[i], y=self.y_data[i])
            self.lines[i].setValue(timestamp)


if __name__ == "__main__":
    ApplicationHandler()
