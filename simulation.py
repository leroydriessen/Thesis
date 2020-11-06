from simnibs import sim_struct, run_simnibs, read_msh
from datetime import datetime
import os
import numpy as np


def run(filename, currents):
    s = sim_struct.SESSION()
    s.fields = 'v'
    s.fnamehead = filename
    print(os.path.dirname(filename))
    s.pathfem = '{}/Output_{}'.format(os.path.dirname(filename), datetime.now().strftime("%d-%m-%y_%H:%M:%S"))

    tdcslist = s.add_tdcslist()
    tdcslist.currents = currents
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

    return run_simnibs(s)[0]


def analyse(file):
    results = []
    simulation = read_msh(file)
    elm = simulation.nodes.node_coord
    weights = simulation.nodes_volumes_or_areas()
    for x in [[20, 20, 20], [-30, -30, -30], [10, -20, 30]]:
        roi = np.linalg.norm(elm - x, axis=1) < 5
        results.append(np.average(simulation.field['v'][:][roi], weights=weights[roi]))
    return results
