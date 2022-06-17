import cv2
import numpy as np
import logging
import json

from fastmot.utils.visualization import get_color


LOGGER = logging.getLogger(__name__)

class TrackedPath:
    def __init__(self, id, suppression=0):
        self.id = id
        self.suppression = suppression

class DuplicateSuppressor():
    def __init__(self, suppression_frames = None):
        self.suppression_frames = 10 if suppression_frames == None else suppression_frames
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

class BoundaryDetector:
    total_count = 0
    def __init__(self, line_pairs, enter_from_left=True, suppression_frames = None, color = None):
        self.id = BoundaryDetector.total_count
        BoundaryDetector.total_count += 1
        if color == None:
            self.color = get_color(self.id)
        else:
            self.color = color
        self.thickness = 6
        self.enter_count = 0
        self.exit_count = 0
        self.enter_from_left = enter_from_left # As viewed from last_two_tracksnt B to A, where Bx >= Ax
        self.line_pairs = line_pairs # [((p0x, p0y), (p1x, p1y)), ...]
        self.ds = DuplicateSuppressor(suppression_frames)

    
    def intersect(self, last_two_tracks):
        if self.is_above_line(last_two_tracks[1]) and not self.is_above_line(last_two_tracks[0]):
            return 1
        elif not self.is_above_line(last_two_tracks[1]) and self.is_above_line(last_two_tracks[0]):
            return -1
        else:
            return 0
    
    def is_above_line(self, point):
        return np.cross(np.asarray(point)-np.asarray(self.line_pairs[0]), np.asarray(self.line_pairs[1])-np.asarray(self.line_pairs[0])) > 0


    def process(self, last_two_tracks, track_id):
        self.ds.step()
        if self.ds.check_unsuppressed(track_id):
            if (self.intersect(last_two_tracks) == 1 and self.enter_from_left) or (self.intersect(last_two_tracks) == -1 and not self.enter_from_left):
                LOGGER.info(f"Enter Room:   person      {track_id}")
                self.enter_count += 1
            elif(self.intersect(last_two_tracks) == 1 and not self.enter_from_left) or (self.intersect(last_two_tracks) == -1 and self.enter_from_left):
                LOGGER.info(f"Exit Room:    person      {track_id} ")
                self.exit_count += 1
            else:
                return
            self.ds.suppress(track_id)