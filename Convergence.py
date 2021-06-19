import logging
import locale
from simnibs import read_msh, sim_struct, run_simnibs
import numpy as np
import shutil
import os
from gmsh_api import gmsh

logging.disable(logging.INFO)
logging.disable(25)  # SUMMARY logging
logging.disable(logging.WARNING)

mri = False  # Do convergence study on MRI (True) or non-MRI (False) data
anode_center = [67.797401, 12.015621, 65.832596]
cathode_center = [-64.055664, 10.183576, 66.089241]
ROI_center = [[49, 0, -0.5], [-49, 2, 0.5]]
ROI_radius = 10.

if mri:
    # resolutions start with ideal value
    resolutions = ["0.70", "0.20", "0.25", "0.30", "0.35", "0.40", "0.45", "0.50", "0.55", "0.60", "0.65"]
    base = "models/MRI/ernie_models/ernie"
else:
    resolutions = ["7", "3", "4", "5", "5.5", "6", "6.5", "7"]
    #resolutions = ["200", "16", "32", "64", "100", "128", "200", "256", "300", "384"]
    base = "Cylinder"

for x in resolutions:
    filename = "/home/leroy/" + x + base + ".msh"
    file = os.path.basename(filename)
    if not os.path.isfile("/home/leroy/" + x + base + ".msh"):
        gmsh.initialize()

        gmsh.merge("/home/leroy/" + x + base + ".stl")
        gmsh.model.geo.addSurfaceLoop([1], 5)
        gmsh.model.geo.addVolume([5], 5)
        gmsh.model.addPhysicalGroup(2, [1], 5)
        gmsh.model.addPhysicalGroup(3, [5], 5)
        gmsh.model.geo.synchronize()
        gmsh.model.mesh.generate(3)
        old_locale = locale.getlocale(locale.LC_NUMERIC)
        locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.)
        gmsh.option.setNumber("Mesh.Algorithm3D", 4)
        gmsh.option.setNumber("Mesh.Optimize", 1)
        gmsh.write("/home/leroy/" + x + base + ".msh")
        locale.setlocale(locale.LC_NUMERIC, old_locale)
        gmsh.finalize()

        s = sim_struct.SESSION()
        s.open_in_gmsh = False
        s.fields = 'v'
        s.fnamehead = filename
        if not os.path.isdir('convergence_output'):
            os.mkdir('convergence_output')
        if os.path.isdir('convergence_output/{}/'.format(file)):
            shutil.rmtree('convergence_output/{}/'.format(file))
        s.pathfem = 'convergence_output/{}/'.format(file)

        tdcslist = s.add_tdcslist()
        tdcslist.currents = [-3e-3, 3e-3]
        tdcslist.cond[4].value = 0.072

        cathode = tdcslist.add_electrode()
        cathode.channelnr = 1
        cathode.dimensions = [13, 13]
        cathode.shape = 'ellipse'
        cathode.thickness = [1, 1]
        cathode.centre = [-31, -33, 1.5]

        anode = tdcslist.add_electrode()
        anode.channelnr = 2
        anode.dimensions = [13, 13]
        anode.shape = 'ellipse'
        anode.thickness = [1, 1]
        anode.centre = [0, 5, 22]

        run_simnibs(s)

########################################################################################################################
    head_mesh = read_msh("convergence_output/" + file + "/" + os.path.splitext(file)[0] + "_TDCS_1_scalar.msh")

    gray_matter = head_mesh.crop_mesh(5)

    elm_centers = gray_matter.nodes.node_coord
    elm_vols = gray_matter.nodes_volumes_or_areas()
    ROI = np.linalg.norm(elm_centers - ROI_center[0], axis=1) < ROI_radius
    ROI2 = np.linalg.norm(elm_centers - ROI_center[1], axis=1) < ROI_radius

    field_name = 'v'
    field = gray_matter.field[field_name]

    measurement = np.average(field[ROI], weights=elm_vols[ROI])
    measurement2 = np.average(field[ROI2], weights=elm_vols[ROI2])
    measurement = measurement - measurement2

    # _, indices = head_mesh.nodes.find_closest_node([[-1, 49, 0.5], [49, 0, -0.5]], True)
    # measurement = head_mesh.field['v'][indices]
    # measurement = measurement[1]-measurement[0]

    if x == resolutions[0]:
        ref = measurement
    else:
        print(100*abs(measurement/ref - 1))
        # print("Resolution " + x + ":\t" + str(100*abs(measurement/ref - 1))+"% deviation from resolution 7")
