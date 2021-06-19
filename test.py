import locale
from gmsh_api import gmsh
import logging
import os
import shutil
from simnibs import sim_struct, run_simnibs, read_msh

# gmsh.initialize()
#
# gmsh.merge("/home/leroy/testPhantom2.stl")
# gmsh.merge("/home/leroy/testPhantom.stl")
# gmsh.model.geo.addSurfaceLoop([1], 2)
# gmsh.model.geo.addSurfaceLoop([2], 5)
# gmsh.model.geo.addVolume([2], 2)
# gmsh.model.geo.addVolume([5, 2], 5)
# gmsh.model.addPhysicalGroup(2, [1], 2)
# gmsh.model.addPhysicalGroup(2, [2], 5)
# gmsh.model.addPhysicalGroup(3, [2], 2)
# gmsh.model.addPhysicalGroup(3, [5], 5)
# gmsh.model.geo.synchronize()
# gmsh.model.mesh.generate(3)
# old_locale = locale.getlocale(locale.LC_NUMERIC)
# locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')
# gmsh.option.setNumber("Mesh.MshFileVersion", 2.)
# gmsh.write("/home/leroy/testCylinder.msh")
# locale.setlocale(locale.LC_NUMERIC, old_locale)
# gmsh.finalize()

logging.disable(logging.INFO)
logging.disable(25)  # SUMMARY logging
logging.disable(logging.WARNING)

for x in [0.066]:
    s = sim_struct.SESSION()
    s.open_in_gmsh = True
    s.fields = 'v'
    s.fnamehead = "/home/leroy/testCylinder.msh"
    if not os.path.isdir('output/'+str(x)):
        os.mkdir('output/'+str(x))
    else:
        shutil.rmtree('output/'+str(x))
    s.pathfem = 'output/'+str(x)

    tdcslist = s.add_tdcslist()
    tdcslist.currents = [-3e-3, 3e-3]
    tdcslist.cond[1].value = x
    tdcslist.cond[4].value = 2

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

    simulation = read_msh("output/"+str(x)+"/testCylinder_TDCS_1_scalar.msh")

    _, indices = simulation.nodes.find_closest_node([[-49, -2, 0.5], [-1, 49, 0.5], [49, 0, -0.5]], True)
    sensors = simulation.field['v'][indices]
    # print("Offset: " + str(x) + ":")
    # print(sensors[0])
    # print(sensors[1])
    print(sensors[2]-sensors[1])
    print(sensors[2]-sensors[0])
