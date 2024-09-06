import cv2
import numpy as np
import supervision as sv
from utils import crowd_counting

# Function to add text with background


def add_text_with_background(frame, text, org, font, font_size, font_color, bg_color, thickness, padding):
    # Calculate text size and baseline
    (text_width, text_height), baseline = cv2.getTextSize(
        text, font, font_size, thickness)

    # Calculate background rectangle coordinates
    bg_tl = (org[0] - padding, org[1] - text_height - padding)
    bg_br = (org[0] + text_width + padding, org[1] + padding)

    # Draw background rectangle
    cv2.rectangle(frame, bg_tl, bg_br, bg_color, -1)

    # Add text on top of the background
    cv2.putText(frame, text, org, font, font_size,
                font_color, thickness, cv2.LINE_AA)


def camInfer(frame: np.ndarray, result, frame_index: int, config):
    # Detect
    detections = result
    detections = detections[np.isin(
        detections.class_id, config.selected_classes)]
    detections = config.tracker.update_with_detections(detections)
    detections = config.smoother.update_with_detections(detections)
    mask = config.zone.trigger(detections=detections)
    detections_inzone = detections[mask]
    anchor = detections_inzone.get_anchors_coordinates(sv.Position.CENTER)

    # Create labels for detected object
    # labels = [
    #     f"#{tracker_id} {class_name}"
    #     for class_name, tracker_id, confidence
    #     in zip(result['class_name'], detections.tracker_id, detections.confidence)
    # ]

    # Crowd in zone
    density = (round(config.zone.current_count / config.area, 2))
    max_density = config.density
    density_quartile = density / max_density

    if density_quartile >= 0.75:
        color = sv.Color.RED  # Highest density range
    elif density_quartile >= 0.5:
        color = sv.Color(r=235, g=113, b=52)  # Medium-high density range
    elif density_quartile >= 0.25:
        color = sv.Color.YELLOW  # Medium-low density range
    else:
        color = sv.Color.GREEN  # Lowest density range

    # Set colors for annotators
    config.box_annotator.color = color
    config.label_annotator.color = color
    config.trace_annotator.color = color

    # Prepare color text for annotation
    color_text = (color.b, color.g, color.r)

    # Text
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_size = config.text_size
    font_color = color_text
    bg_color = (0, 0, 0)
    thickness = config.text_thickness
    padding = 6

    # Annotate frame with appropriate color
    if density_quartile >= 0.75:
        text = "WARNING!!!"
        org = (config.text_position_x, config.text_position_y4)
        annotated_frame = frame.copy()
        add_text_with_background(annotated_frame, text, org, font,
                                 font_size, font_color, bg_color, thickness, padding)
    else:
        annotated_frame = frame.copy()

    # Micro-crowd
    # crowds = crowd_counting(anchor, int(config.width),
    #                         int(config.height), config.min_distance)
    # for crowd in crowds:
    #     if crowd['crowd_counting'] >= config.max_crowd:
    #         polygons = np.array([crowd['polygon_coordinates']])
    #         sv.draw_polygon(annotated_frame, polygons,
    #                         color=sv.Color.YELLOW, thickness=2)

    # Annotations
    config.box_annotator.annotate(
        annotated_frame, detections=detections)
    config.label_annotator.annotate(
        annotated_frame, detections=detections)
    config.trace_annotator.annotate(
        annotated_frame, detections=detections)
    config.zone_annotator.annotate(
        annotated_frame)

    text = f"FPS {config.fpsNow:.2f} ({config.delay:.2f}ms)"
    org = (config.text_position_x, config.text_position_y)
    add_text_with_background(annotated_frame, text, org, font,
                             font_size, font_color, bg_color, thickness, padding)

    text = f"Population (zone): {config.zone.current_count}"
    org = (config.text_position_x, config.text_position_y2)
    add_text_with_background(annotated_frame, text, org, font,
                             font_size, font_color, bg_color, thickness, padding)

    text = f"Density: {density:.2f}/m^2"
    org = (config.text_position_x, config.text_position_y3)
    add_text_with_background(annotated_frame, text, org, font,
                             font_size, font_color, bg_color, thickness, padding)

    # Text Outline
    # cv2.putText(annotated_frame, f"Population (zone): {config.zone.current_count}", (config.text_position_x, config.text_position_y2),
    #             cv2.FONT_HERSHEY_SIMPLEX, config.text_size, (0, 0, 0), config.text_thickness+1, cv2.LINE_AA)
    # cv2.putText(annotated_frame, f"Density: {density:.2f}/m^2", (config.text_position_x, config.text_position_y3),
    #             cv2.FONT_HERSHEY_SIMPLEX, config.text_size, (0, 0, 0), config.text_thickness+1, cv2.LINE_AA)
    # cv2.putText(annotated_frame, f"Speed: {config.delay:.2f}ms", (config.text_position_x, config.text_position_y),
    #             cv2.FONT_HERSHEY_SIMPLEX, config.text_size, (0, 0, 0), config.text_thickness+1, cv2.LINE_AA)

    # # Text
    # cv2.putText(annotated_frame, f"Population (zone): {config.zone.current_count}", (config.text_position_x, config.text_position_y2),
    #             cv2.FONT_HERSHEY_SIMPLEX, config.text_size, color_text, config.text_thickness, cv2.LINE_AA)
    # cv2.putText(annotated_frame, f"Density: {density:.2f}/m^2", (config.text_position_x, config.text_position_y3),
    #             cv2.FONT_HERSHEY_SIMPLEX, config.text_size, color_text, config.text_thickness, cv2.LINE_AA)
    # cv2.putText(annotated_frame, f"Speed: {config.delay:.2f}ms", (config.text_position_x, config.text_position_y),
    #             cv2.FONT_HERSHEY_SIMPLEX, config.text_size, color_text, config.text_thickness, cv2.LINE_AA)

    return annotated_frame
