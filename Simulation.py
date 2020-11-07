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
    def __init__(self, filename, currents, electrodes, sizes=None):
        super(Simulation, self).__init__()
        self.filename = filename
        self.currents = currents
        self.electrodes = electrodes
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
        s.pathfem = '{}/Output_{}'.format(os.path.dirname(self.filename), datetime.now().strftime("%d-%m-%y_%H:%M:%S"))

        tdcslist = s.add_tdcslist()
        tdcslist.currents = self.currents
        # tdcslist.cond[1].value = 2
        # tdcslist.cond[4].value = 0.01

        cathode = tdcslist.add_electrode()
        cathode.channelnr = 1
        cathode.dimensions = [50, 70]
        cathode.shape = 'rect'
        cathode.thickness = 5
        cathode.centre = [-64.129707, 10.149533, 66.025742]  # 'C3'
        # cathode.pos_ydir = 'Cz'

        anode = tdcslist.add_electrode()
        anode.channelnr = 2
        anode.dimensions = [30, 30]
        anode.shape = 'ellipse'
        anode.thickness = 5
        anode.centre = [67.828148, 11.505963, 65.788376]  # 'C4'

        anode = tdcslist.add_electrode()
        anode.channelnr = 3
        anode.dimensions = [30, 30]
        anode.shape = 'rect'
        anode.thickness = 5
        anode.centre = [67.828148, 11.505963, -65.788376]  # 'C4 mirror'

        file = run_simnibs(s)[0]

        simulation = read_msh(file)

        if self.sizes is None:
            electrodes = np.array(self.electrodes)
            closest, indices = simulation.nodes.find_closest_node(electrodes, True)
            results = simulation.field['v'][indices]
        else:
            results = []
            elm = simulation.nodes.node_coord
            weights = simulation.nodes_volumes_or_areas()
            for i, x in enumerate(self.electrodes):
                roi = np.linalg.norm(elm - x, axis=1) < self.sizes[i]
                if max(roi) is False:
                    results.append(0)
                else:
                    results.append(np.average(simulation.field['v'][roi], weights=weights[roi]))
        shutil.rmtree(os.path.dirname(file))

        self.communication.peak.emit(np.array(results))
