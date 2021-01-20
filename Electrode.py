from simnibs.simulation import ELECTRODE


class Electrode(ELECTRODE):
    def __init__(self, readable, writable, x, y, z, shape, dim, thick, name="Unnamed Electrode"):
        super(Electrode, self).__init__()

        self.readable = readable
        self.writeable = writable
