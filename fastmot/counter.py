import cv2
import numpy as np
import logging

from fastmot.utils.rect import get_bottom_center

LOGGER = logging.getLogger(__name__)

class TrackedTrajectory:
    def __init__(self, id):
        self.id = id


class Counter:
    def __init__(self):
        self.line = ((579, 465),(766, 450))
        self.np_line = np.asarray(self.line)
        self.line_color = (0, 170, 0)
        self.thickness = 6

    def step(self, tracks):
        for track in tracks:
            # bottom_center = get_bottom_center(track.tlbr)
            tlbrs = np.reshape(list(track.bboxes), (len(track.bboxes), 4))
            bottom_centers = tuple(map(lambda box: get_bottom_center(box), tlbrs[::4]))
            latest_bottom_center = bottom_centers[-1]
            LOGGER.info(f"{track.trk_id} {bottom_centers} {self.is_above_line(latest_bottom_center)}")


    def draw_line(self, frame):
        cv2.line(frame, self.line[0], self.line[1], self.line_color, self.thickness) 

    def is_above_line(self, point):
        return np.cross(np.asarray(point)-self.np_line[0], self.np_line[1]-self.np_line[0]) > 0

