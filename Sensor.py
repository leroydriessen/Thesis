from PyQt5.QtCore import QRunnable
import time
import random


class Sensor(QRunnable):
    def __init__(self, dataclass, starttime):
        super(Sensor, self).__init__()
        self.data = dataclass
        self.starttime = starttime

    def run(self):
        while True:
            time.sleep(random.uniform(0.01, 0.1))
            self.data.append(time.time()-self.starttime, random.gauss(0.1, 0.03))
