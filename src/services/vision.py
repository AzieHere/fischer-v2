import numpy as np
import config


class Vision:
    def __init__(self, camera):
        self.camera = camera

    def get_frame(self):
        return self.camera.get_latest_frame_view()

    @staticmethod
    def search_row(frame, y, color):
        start_y = config.REGION[1]
        y -= start_y

        tol = color[3]
        target = color[:3]

        row = frame[y, :, :3].astype(np.int16)

        diff = row - target
        dist = (diff * diff).sum(axis=1)

        tol_sq = tol * tol
        return np.flatnonzero(dist <= tol_sq)

    @staticmethod
    def search(frame, y0, y1, color):
        start_y = config.REGION[1]
        y0 -= start_y
        y1 -= start_y

        tol = color[3]
        target = color[:3]

        region = frame[y0:y1, :, :3].astype(np.int16)

        diff = region - target
        dist = (diff * diff).sum(axis=2)

        return np.flatnonzero(np.any(dist <= tol * tol, axis=0))

    @staticmethod
    def squared_dist(a, b):
        diff = a[:3].astype(np.int16) - b[:3].astype(np.int16)
        return int((diff * diff).sum())
