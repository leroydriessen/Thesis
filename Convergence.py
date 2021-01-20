import logging
from simnibs import read_msh, sim_struct, run_simnibs
import numpy as np
import shutil
import os

logging.disable(logging.INFO)
logging.disable(25)  # SUMMARY logging
logging.disable(logging.WARNING)

mri = False  # Do convergence study on MRI (True) or non-MRI (False) data
anode_center = [67.797401, 12.015621, 65.832596]
cathode_center = [-64.055664, 10.183576, 66.089241]
ROI_center = [2.504336, 117.433159, 20.609865]
ROI_radius = 20.

if mri:
    # resolutions start with ideal value
    resolutions = ["0.70", "0.20", "0.25", "0.30", "0.35", "0.40", "0.45", "0.50", "0.55", "0.60", "0.65"]
    base = "models/MRI/ernie_models/ernie"
else:
    resolutions = ["400", "16", "32", "64", "100", "128", "200", "256", "300", "384"]
    base = "models/nonMRI/sphere_models/sphere"

for x in resolutions:
    filename = base + x + ".msh"
    file = os.path.basename(filename)

    s = sim_struct.SESSION()
    s.open_in_gmsh = True
    s.fields = 'v'
    s.fnamehead = filename
    if not os.path.isdir('convergence_output'):
        os.mkdir('convergence_output')
    if os.path.isdir('convergence_output/{}/'.format(file)):
        shutil.rmtree('convergence_output/{}/'.format(file))
    s.pathfem = 'convergence_output/{}/'.format(file)

    tdcslist = s.add_tdcslist()
    tdcslist.currents = [-1e-3, 1e-3]
    # tdcslist.cond[1].value = 2
    # tdcslist.cond[4].value = 0.01

    cathode = tdcslist.add_electrode()
    cathode.channelnr = 1
    cathode.dimensions = [50, 70]
    cathode.shape = 'rect'
    cathode.thickness = 5
    cathode.centre = cathode_center

    anode = tdcslist.add_electrode()
    anode.channelnr = 2
    anode.dimensions = [30, 30]
    anode.shape = 'ellipse'
    anode.thickness = 5
    anode.centre = anode_center

    run_simnibs(s)

########################################################################################################################
    head_mesh = read_msh("convergence_output/" + file + "/" + os.path.splitext(file)[0] + "_TDCS_1_scalar.msh")

    gray_matter = head_mesh.crop_mesh(5)

    elm_centers = gray_matter.elements_baricenters()[:]
    elm_vols = gray_matter.elements_volumes_and_areas()[:]
    ROI = np.linalg.norm(elm_centers - ROI_center, axis=1) < ROI_radius

    field_name = 'normE'
    field = gray_matter.field[field_name][:]

    mean_normE = np.average(field[ROI], weights=elm_vols[ROI])

    if x == resolutions[0]:
        ref = mean_normE
    else:
        print(100*abs(mean_normE/ref - 1))
