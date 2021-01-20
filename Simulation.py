from simnibs import sim_struct, run_simnibs, read_msh
from datetime import datetime
import os
import shutil
import numpy as np
import logging
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal


class SimulationData(QObject):
    peak = pyqtSignal(object)


class Simulation(QRunnable):
    def __init__(self, filename, currents, stimulators, observers, sizes=None):
        super(Simulation, self).__init__()
        self.filename = filename
        self.currents = currents
        self.stimulators = stimulators
        self.observers = observers
        self.sizes = sizes
        self.communication = SimulationData()

    def run(self):
        logging.disable(logging.INFO)
        logging.disable(25)
        logging.disable(logging.WARNING)

        s = sim_struct.SESSION()
        s.open_in_gmsh = False
        s.fields = 'v'
        s.fnamehead = self.filename
        if os.path.isdir("tmp"):
            shutil.rmtree("tmp")
        s.pathfem = "tmp"

        tdcslist = s.add_tdcslist()
        tdcslist.currents = self.currents

        # tdcslist.cond[1].value = 2
        # tdcslist.cond[4].value = 0.01

        for electrode in self.stimulators:
            tdcslist.add_electrode(electrode)

        file = run_simnibs(s)[0]

        simulation = read_msh(file)

        if self.sizes is None:
            sensors = [observer.centre for observer in self.observers]
            closest, indices = simulation.nodes.find_closest_node(sensors, True)
            results = simulation.field['v'][indices]
        else:
            results = []
            elm = simulation.nodes.node_coord
            weights = simulation.nodes_volumes_or_areas()
            for i, x in enumerate(self.observers):
                roi = np.linalg.norm(elm - x, axis=1) < self.sizes[i]
                if max(roi) is False:
                    results.append(0)
                else:
                    results.append(np.average(simulation.field['v'][roi], weights=weights[roi]))
        shutil.rmtree(os.path.dirname(file))

        self.communication.peak.emit(np.array(results))
