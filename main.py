import gmsh_api.gmsh as gmsh
import os.path
from simnibs import sim_struct, run_simnibs
from datetime import datetime

filename = 'sphere'

if not os.path.isfile('models/nonMRI/{0}/{0}.msh'.format(filename)):
    print("{0}.msh file does not exist yet, creating one from .stl files".format(filename))
    gmsh.initialize()
    current = 1
    if not os.path.isfile('models/nonMRI/{0}/{0}Scalp.stl'.format(filename)):
        raise FileNotFoundError("Scalp stl file does not exist")
    gmsh.merge('models/nonMRI/{0}/{0}Scalp.stl'.format(filename))
    gmsh.model.geo.addSurfaceLoop([current], 5)
    gmsh.model.geo.addVolume([5], 5)
    print("Added Scalp information")
    current = current + 1
    if os.path.isfile('models/nonMRI/{0}/{0}Skull.stl'.format(filename)):
        gmsh.merge('models/nonMRI/{0}/{0}Skull.stl'.format(filename))
        gmsh.model.geo.addSurfaceLoop([current], 4)
        gmsh.model.geo.addVolume([4], 4)
        print("Added Skull information")
        current = current + 1
    if os.path.isfile('models/nonMRI/{0}/{0}Brain.stl'.format(filename)):
        gmsh.merge('models/nonMRI/{0}/{0}Brain.stl'.format(filename))
        gmsh.model.geo.addSurfaceLoop([current], 2)
        gmsh.model.geo.addVolume([2], 2)
        print("Added Brain information")
    gmsh.model.geo.synchronize()
    print("Generating mesh...")
    gmsh.model.mesh.generate(3)
    print("Writing mesh")
    gmsh.write('models/nonMRI/{0}/{0}.msh'.format(filename))
    gmsh.finalize()
    print("Successfully created {0}.msh".format(filename))
else:
    print("Found {0}.msh".format(filename))

s = sim_struct.SESSION()
s.fnamehead = 'models/nonMRI/{0}/{0}.msh'.format(filename)
s.pathfem = 'outputs/output_{}/'.format(datetime.now().strftime("%d-%m-%y_%H:%M"))

tdcslist = s.add_tdcslist()
tdcslist.currents = [-1e-3, 1e-3]
tdcslist.cond[1].value = 2
tdcslist.cond[4].value = 0.01

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

run_simnibs(s)
