import locale
from gmsh_api import gmsh
import os
from PyQt5.QtCore import QRunnable, QObject, pyqtSignal


class MeshCommunication(QObject):
    status_info = pyqtSignal(str)
    filename = pyqtSignal(str)


class MeshCreation(QRunnable):
    def __init__(self, filename):
        super(MeshCreation, self).__init__()
        self.filename = filename
        self.communication = MeshCommunication()

    def run(self):
        dir_name = os.path.dirname(self.filename) + "/"
        model = os.path.splitext(os.path.basename(self.filename))[0].rsplit("Scalp")[0]
        self.communication.status_info.emit("Creating a mesh of " + model)

        layers = []
        gmsh.initialize()

        if os.path.isfile(dir_name + model + "Brain.stl"):
            gmsh.merge(dir_name + model + "Brain.stl")
            gmsh.model.geo.addSurfaceLoop([len(layers) + 1], 2)
            layers.append(2)
        if os.path.isfile(dir_name + model + "Skull.stl"):
            gmsh.merge(dir_name + model + "Skull.stl")
            gmsh.model.geo.addSurfaceLoop([len(layers) + 1], 4)
            layers.append(4)

        gmsh.merge(self.filename)
        gmsh.model.geo.addSurfaceLoop([len(layers) + 1], 5)
        layers.append(5)

        if layers == [2, 4, 5]:
            gmsh.model.geo.addVolume([5, 4], 5)
            gmsh.model.geo.addVolume([4, 2], 4)
            gmsh.model.geo.addVolume([2], 2)
        elif layers == [2, 5]:
            gmsh.model.geo.addVolume([5, 2], 5)
            gmsh.model.geo.addVolume([2], 2)
        elif layers == [5]:
            gmsh.model.geo.addVolume([5], 5)

        gmsh.model.geo.synchronize()
        self.communication.status_info.emit("Meshing " + str(len(layers)) + "-layered head... (can take a while)")

        gmsh.model.mesh.generate(3)
        old_locale = locale.getlocale(locale.LC_NUMERIC)
        locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')
        self.communication.status_info.emit("Writing mesh file... (can take a while)")
        gmsh.write(dir_name + model + ".msh")
        locale.setlocale(locale.LC_NUMERIC, old_locale)
        gmsh.finalize()
        self.communication.filename.emit(dir_name + model + ".msh")
