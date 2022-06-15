import cv2
import numpy as np
import logging

from fastmot.utils.rect import get_bottom_center

LOGGER = logging.getLogger(__name__)

color_gilded = (78, 219, 247)
color_aqua_lake = (153, 149, 47)


class TrackedPath:
    def __init__(self, id, suppression=0):
        self.id = id
        self.suppression = suppression

class DuplicateSuppressor():
    def __init__(self, suppression_frames = 10):
        self.suppression_frames = suppression_frames
        self.suppressed_paths = []

    def suppress(self, id):
        if not self.suppressed_contains(id):
            path = TrackedPath(id, self.suppression_frames)
        self.suppressed_paths.append(path)

    def suppressed_contains(self, id):
        for path in self.suppressed_paths:
            if id == path.id:
                return True
        return False

    def check_unsuppressed(self, id):
        if self.suppressed_contains(id):
            return False
        else:
            return True

    def step(self):
        delete_indices = []
        for index, path in enumerate(self.suppressed_paths):
            if path.suppression > 0:
                path.suppression -= 1
            else:
                delete_indices.append(index)
        for index in reversed(delete_indices):
            self.suppressed_paths.pop(index)


class Counter:
    def __init__(self):
        self.line = ((579, 465),(766, 450))
        self.np_line = np.asarray(self.line)
        self.line_color = (0, 170, 0)
        self.thickness = 6
        self.tracked_paths = []
        self.enter_count = 0
        self.exit_count = 0
        self.ds = DuplicateSuppressor(120)

    def step(self, frame, tracks):
        self.ds.step()
        self.draw_info(frame)
        for track in tracks:
            tlbrs = np.reshape(list(track.bboxes), (len(track.bboxes), 4))
            bottom_centers = tuple(map(lambda box: get_bottom_center(box), tlbrs[::4]))
            poi = bottom_centers[-2:] #Get latest 2 points to check if line is crossed 
            
            if self.ds.check_unsuppressed(track.trk_id):
                if self.is_above_line(poi[1]) and not self.is_above_line(poi[0]):
                    self.ds.suppress(track.trk_id)
                    LOGGER.info(f"Enter Room:   person      {track.trk_id}")
                    self.enter_count += 1
                elif not self.is_above_line(poi[1]) and self.is_above_line(poi[0]):
                    self.ds.suppress(track.trk_id)
                    LOGGER.info(f"Exit Room:    person      {track.trk_id} ")
                    self.exit_count += 1
        
        

    @staticmethod
    def get_bottom_centers(track):
        tlbrs = np.reshape(list(track.bboxes), (len(track.bboxes), 4))
        bottom_centers = tuple(map(lambda box: get_bottom_center(box), tlbrs[::4]))

    def draw_info(self, frame):
        cv2.line(frame, self.line[0], self.line[1], self.line_color, self.thickness)
        cv2.rectangle(frame, (413, 215), (557,263), color_gilded, -1) 
        cv2.rectangle(frame, (413, 287), (557,335), color_aqua_lake, -1)
        cv2.putText(frame, f"Enter: {self.enter_count}", (418, 251), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Exit:  {self.exit_count}", (418, 323), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)

    def is_above_line(self, point):
        return np.cross(np.asarray(point)-self.np_line[0], self.np_line[1]-self.np_line[0]) > 0

