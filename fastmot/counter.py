import cv2
import numpy as np
import logging
import json
from fastmot.boundary_detector import BoundaryDetector

LOGGER = logging.getLogger(__name__)
               

class Counter:
    def __init__(self, boundary_cfg_path, frame_size, draw=True):
        self.bd_list = self.populate_bd_list(boundary_cfg_path, frame_size)
        self.draw = draw

    def populate_bd_list(self, boundary_cfg_path, frame_size):
        bd_list = []
        f = open(boundary_cfg_path)
        line_pairs = json.load(f)['line_pairs']

        for lp in line_pairs:
            c = lp['coordinates']
            coords = ((int(c['x0']), int(c['y0'])), (int(c['x1']), int(c['y1'])))
            efl = lp['properties']['enter_from_left']
            sf = lp['properties']['suppression_frames']
            bd = BoundaryDetector(coords, enter_from_left = efl, suppression_frames=sf)
            LOGGER.info(f"Creating Boundary at {coords}")
            bd_list.append(bd)
        
        return bd_list


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



