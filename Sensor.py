from PyQt5.QtCore import QRunnable
import time
import random


class Sensor(QRunnable):
    def __init__(self, dataclass, start_time, end_time):
        super(Sensor, self).__init__()
        self.data = dataclass
        self.start_time = start_time
        self.end_time = end_time
        self.cancelled = False

    def run(self):
        timestamp = 0
        while not self.cancelled and timestamp < self.end_time:
            timestamp = time.time() - self.start_time
            time.sleep(random.uniform(0.1, 0.5))
            self.data.append(timestamp, random.gauss(-0.01, 0.005))

    def cancel(self):
        self.cancelled = True
