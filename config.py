import math
import numpy as np
import supervision as sv
from ultralytics import YOLO


class Config:
    def __init__(self, polygon=None, model='Model/model.engine', confidence=0.45, iou=0.5, max_crowd=4, crowd_distance=80, population=100, area=100, density=4.7, width=1920, height=1080, fps=30):

        # Load a model
        self.model = YOLO(model)

        # Check if polygon is None
        if polygon is None:
            print("No polygon was passed. Using full area detections.")
            self.polygon = np.array([
                [0, 0],
                [int(width), 0],
                [int(width), int(height)],
                [0, int(height)]
            ])
            polygon = self.polygon

        # Check if polygon is a NumPy array
        if not isinstance(polygon, np.ndarray):
            print("Polygon is not a NumPy array.")
            return

        # Check if polygon has the right shape (N, 2) where N >= 3
        if polygon.ndim != 2 or polygon.shape[1] != 2 or polygon.shape[0] < 3:
            print(
                "Polygon does not have the correct format or enough points. It must contains [[x,y],[x,y],[x,y]] at least.")
            return

        self.polygon = polygon

        # Parameters
        self.max_population = population
        self.area = area
        self.min_distance = crowd_distance  # pixels
        self.max_crowd = max_crowd
        self.confidence = confidence
        self.iou = iou
        self.density = density
        self.color = sv.Color.GREEN
        self.width = int(width)
        self.height = int(height)
        self.fps = fps
        self.delay = 0
        self.fpsNow = 0

        # Scaling
        text_size_scale = min(width,
                              height) / 1000.0
        thickness_scale = min(width,
                              height) / 1000.0
        text_position_scale_x = width / 1280.0
        text_position_scale_y = height / 720.0

        # Adjust text size and position based on scale factors
        self.text_size = max(0.3, (text_size_scale * 1.15))
        self.text_thickness = max(1, int(3 * thickness_scale))
        self.text_position_x = int(
            width * 0.015)
        self.text_position_y = int(
            height * 0.06)
        self.text_position_y2 = int(
            height * 0.12)
        self.text_position_y3 = int(
            height * 0.18)
        self.text_position_y4 = int(
            height * 0.24)
        poly_text = 0.8*self.text_size
        label_text = 0.6*self.text_size

        # Declare annotators
        self.fps_monitor = sv.FPSMonitor()
        self.tracker = sv.ByteTrack()
        self.smoother = sv.DetectionsSmoother(length=1)
        self.box_annotator = sv.BoundingBoxAnnotator(
            thickness=2, color=self.color)
        self.label_annotator = sv.LabelAnnotator(
            color=self.color, text_scale=label_text, text_padding=max(1, math.ceil(label_text*12)))
        self.trace_annotator = sv.TraceAnnotator(
            thickness=2, color=self.color, trace_length=12)
        self.zone = sv.PolygonZone(
            polygon=self.polygon, frame_resolution_wh=(self.width, self.height), triggering_anchors=(sv.Position.CENTER,))
        self.zone_annotator = sv.PolygonZoneAnnotator(
            zone=self.zone, color=sv.Color.RED, thickness=max(1, math.ceil(poly_text*5)), text_thickness=max(1, math.ceil(poly_text)), text_scale=poly_text, text_padding=max(1, math.ceil(poly_text*12)))
        self.selected_classes = [0]
