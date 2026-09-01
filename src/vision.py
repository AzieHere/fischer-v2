import numpy as np
import config


class Vision:
    def __init__(self, camera):
        self.camera = camera

    def get_frame(self):
        return self.camera.get_latest_frame_view()

    @staticmethod
    def search_row(frame, y, color, tolerance=5):
        start_y = config.REGION[1]
        tolerance = color[3]

        y -= start_y

        row = frame[y, :, :3]
        diff = np.abs(row - color[:3])

        return np.flatnonzero(np.all(diff <= tolerance, axis=1))

    @staticmethod
    def squared_dist(a, b):
        d0 = int(a[0]) - int(b[0])
        d1 = int(a[1]) - int(b[1])
        d2 = int(a[2]) - int(b[2])

        return d0 * d0 + d1 * d1 + d2 * d2
