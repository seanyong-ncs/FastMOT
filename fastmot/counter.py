import cv2
import numpy as np
import logging

from fastmot.utils.visualization import get_color
from fastmot.utils.rect import get_bottom_center

LOGGER = logging.getLogger(__name__)

color_gilded = (78, 219, 247)
color_aqua_lake = (153, 149, 47)


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
    def __init__(self, line_pairs, enter_from_left=True, suppression_frames = None):
        self.id = BoundaryDetector.total_count
        BoundaryDetector.total_count += 1
        self.color = get_color(self.id)
        self.thickness = 6
        self.enter_count = 0
        self.exit_count = 0
        self.enter_from_left = enter_from_left # As viewed from last_two_tracksnt B to A, where Bx >= Ax
        self.line_pairs = line_pairs # [((p0x, p0y), (p1x, p1y)), ...]
        self.ds = DuplicateSuppressor(suppression_frames)

    
    def intersect(self, last_two_tracks):
        if self.is_above_line(last_two_tracks[1]) and not self.is_above_line(last_two_tracks[0]):
            print(1)
            return 1
        elif not self.is_above_line(last_two_tracks[1]) and self.is_above_line(last_two_tracks[0]):
            print(-1)
            return -1
        else:
            return 0
    
    def is_above_line(self, last_two_tracks):
        return np.cross(np.asarray(last_two_tracks)-np.asarray(self.line_pairs[0]), np.asarray(self.line_pairs[1])-np.asarray(self.line_pairs[0])) > 0


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
                
               

class Counter:
    def __init__(self, draw=True):
        self.bd_list = self.populate_bd_list()
        self.draw = draw

    def populate_bd_list(self):
        # Read from file later, hardcode for now
        my_bd = BoundaryDetector(((579, 465),(766, 450)), suppression_frames=90)
        my_bd_2 = BoundaryDetector(((539, 465),(649, 650)), enter_from_left = False, suppression_frames=90)
        return [my_bd, my_bd_2]

    def step(self, frame, tracks):
        if self.draw:
            self.draw_info(frame)

        for track in tracks:
            tlbrs = np.reshape(list(track.bboxes), (len(track.bboxes), 4))
            bottom_centers = tuple(map(lambda box: get_bottom_center(box), tlbrs[::4]))
            last_two_tracks = bottom_centers[-2:] #Get latest 2 last_two_tracks to check if line is crossed
            for bd in self.bd_list:
                bd.process(last_two_tracks, track.trk_id) 

    def draw_info(self, frame):
        for index, bd in enumerate(self.bd_list):
            offset = index * 40
            cv2.line(frame, bd.line_pairs[0], bd.line_pairs[1], bd.color, bd.thickness)
            cv2.rectangle(frame, (10, 10 + offset), (240, 40 + offset), bd.color, -1)
            cv2.putText(frame, f"Enter: {bd.enter_count}", (15, 30 + offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA) 
            cv2.putText(frame, f"Exit: {bd.exit_count}", (145, 30 + offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA) 



