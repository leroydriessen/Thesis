import os
import sys
import time

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
import simnibs

from GUI import Ui_MainWindow
from MeshCreation import MeshCreation
from Sensor import Sensor
from SensorData import SensorData
from Simulation import Simulation


class ApplicationHandler:
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)
        self.MainWindow = QtWidgets.QMainWindow()
        self.filename = ""
        self.ui = Ui_MainWindow()
        self.timer = QtCore.QTimer()
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
        self.x_data = []
        self.y_data = []
        self.sensors = []
        self.electrodes = []
        self.stimulators = []
        self.observers = []
        self.running = False
        self.tmp = []
        self.tmp2 = []

        self.ui.setupUi(self.MainWindow)
        self.ui.actionOpen_mesh.triggered.connect(self.open_msh)
        self.ui.actionCreate_mesh.triggered.connect(self.open_stl)
        self.ui.actionOpen_settings.triggered.connect(self.open_settings)
        self.ui.pushButton.clicked.connect(self.start_stop)
        self.timer.timeout.connect(self.update_graphs)
        self.thread_pool.setExpiryTimeout(5)
        self.MainWindow.show()

        test = self.ui.graphicsView
        test.setBackground((0, 0, 0, 0))
        code = app.exec_()
        for sensor in self.sensors:
            sensor.cancel()
        self.thread_pool.waitForDone()
        sys.exit(code)

    def info(self, text):
        self.ui.info.setText(text)

    def set_file(self, path):
        file = os.path.basename(path)
        if file == "":
            self.ui.pushButton.setEnabled(False)
            info = "No model selected"
        else:
            self.filename = path
            self.ui.pushButton.setEnabled(True)
            info = "Selected: " + file
        self.info(info)
        assert self.ui.pushButton.text() == "Run"

    def open_settings(self):
        settings, _ = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow, "Open settings", "./", "CSV file (*.csv)")
        if settings == "":
            return
        file = open(settings).readlines()
        self.ui.electrodeTable.setRowCount(len(file)-1)
        header = file[0].split(",")
        header = [x.lower().strip("\n") for x in header]
        assert header == ['name', 'read', 'write', 'x', 'y', 'z']

        table = self.ui.electrodeTable
        for i, line in enumerate(file[1:]):
            line = line.split(",")
            line[-1] = line[-1].strip("\n")
            if line[2].lower() == "true":
                electrode = simnibs.simulation.ELECTRODE()
                electrode.name = line[0]
                electrode.centre = [line[3], line[4], line[5]]
                electrode.channelnr = i
                electrode.thickness = 5
                electrode.shape = 'rect'
                electrode.dimensions = [30, 30]
                self.electrodes.append(electrode)

                row = QtWidgets.QTableWidgetItem()
                row.setText(electrode.name)
                table.setVerticalHeaderItem(i, row)

                cell = QtWidgets.QTableWidgetItem()
                cell.setText("0")
                table.setItem(i, 0, cell)

                cell = QtWidgets.QTableWidgetItem()
                if line[1].lower() == "true":
                    cell.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                    cell.setCheckState(QtCore.Qt.Unchecked)
                else:
                    cell.setFlags(QtCore.Qt.ItemIsUserCheckable)
                table.setItem(i, 1, cell)
                # test += 1
                pass
            elif line[2].lower() == "false":
                electrode = simnibs.simulation.ELECTRODE()
                electrode.name = line[0]
                electrode.centre = [line[3], line[4], line[5]]
                self.electrodes.append(electrode)

                row = QtWidgets.QTableWidgetItem()
                row.setText(electrode.name)
                table.setVerticalHeaderItem(i, row)

                cell = QtWidgets.QTableWidgetItem()
                cell.setText("")
                table.setItem(i, 0, cell)

                cell = QtWidgets.QTableWidgetItem()
                if line[1].lower() == "true":
                    cell.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                    cell.setCheckState(QtCore.Qt.Unchecked)
                else:
                    cell.setFlags(QtCore.Qt.ItemIsUserCheckable)
                table.setItem(i, 1, cell)
                pass
            else:
                raise Exception("wow")

        self.ui.electrodeTable.setColumnWidth(1, 20)
        self.ui.electrodeTable.setEnabled(True)

    def open_msh(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow, "Open .msh file", "./", "Msh files (*.msh)")
        self.set_file(filename)

    def open_stl(self):
        scalp_file, _ = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow, "Open scalp .stl file", "./", "3D scalp files (*Scalp.stl)")
        mesh_creation = MeshCreation(scalp_file)
        mesh_creation.communication.status_info.connect(self.info)
        mesh_creation.communication.filename.connect(self.set_file)
        self.thread_pool.start(mesh_creation)

    def end_experiment(self):
        self.info("Finished!")
        self.thread_pool.waitForDone()
        self.timer.stop()
        self.sensors = []
        self.observers = []
        self.stimulators = []
        self.ui.tabWidget.setEnabled(True)
        self.ui.pushButton.setText("Run again")

    def restart(self):
        self.timer.stop()
        self.x_data = []
        self.y_data = []
        for sensor in self.sensors:
            sensor.cancel()
        self.sensors = []
        self.observers = []
        self.stimulators = []
        self.ui.graphicsView.clear()
        self.ui.pushButton.setText("Run")
        self.set_file(self.filename)
        self.lines = []
        self.running = False
        self.ui.tabWidget.setEnabled(True)
        self.thread_pool.waitForDone()

    def start_stop(self):
        if self.running:
            self.restart()
            return
        self.restart()
        self.running = True
        self.info("Simulating model... (can take a while)")

        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton.setCheckable(True)
        self.ui.pushButton.setChecked(True)
        self.ui.tabWidget.setEnabled(False)
        self.ui.pushButton.setText("Stop")

        currents = []
        table = self.ui.electrodeTable
        for x in range(table.rowCount()):
            if table.item(x, 0).text() != '' and table.item(x, 0).text() != '0':
                self.stimulators.append(self.electrodes[x])
                currents.append(float(self.ui.electrodeTable.item(x, 0).text())/1000)
            else:
                if table.item(x, 1).checkState() == QtCore.Qt.Checked:
                    self.observers.append(self.electrodes[x])
        simulation = Simulation(self.filename, currents, self.stimulators, self.observers)
        simulation.communication.peak.connect(self.experiment)
        self.thread_pool.start(simulation)

    def experiment(self, peak):
        self.info("Running...")
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

        self.tmp = y + np.random.normal(0, 0.001, [len(self.observers), len(x)])
        self.tmp2 = x

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

        for i in range(len(self.observers)):
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

        for i in range(len(self.observers)):
            new_data = self.sensors[i].data.getData()

            if new_data is not None:
                plt = test.getItem(i, 0)
                self.x_data[i].extend(new_data[0])
                self.y_data[i].extend(new_data[1])
                # plt.listDataItems()[1].setData(x=self.x_data[i], y=self.y_data[i])
                plt.listDataItems()[1].setData(x=self.tmp2[:int(timestamp*self.freq):4], y=self.tmp[i, :int(timestamp*self.freq):4])
            self.lines[i].setValue(timestamp)


if __name__ == "__main__":
    ApplicationHandler()
