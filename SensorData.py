from PyQt5.QtCore import QObject, QMutex, QMutexLocker


class SensorData(QObject):
    def __init__(self):
        super(SensorData, self).__init__()
        self.mutex = QMutex()
        self.x = []
        self.y = []

    def append(self, time, datapoint):
        QMutexLocker(self.mutex)
        self.x.append(time)
        self.y.append(datapoint)

    def getData(self):
        QMutexLocker(self.mutex)
        assert len(self.x) == len(self.y), "Thread communication failed in sensor data"
        if not self.x:
            return None
        else:
            x = self.x
            y = self.y
            self.x = []
            self.y = []
            return x, y
