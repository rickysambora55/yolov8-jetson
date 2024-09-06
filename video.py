import os
import cv2
import json
import torch
import platform
from inference_cam import *
from config import Config

# Load config data
with open('config.json', 'r') as f:
    data = json.load(f)


def callback(image_slice: np.ndarray, config, device) -> sv.Detections:
    result = config.model.predict(source=image_slice, conf=config.confidence,
                                  iou=config.iou, half=True, imgsz=640, device=device)[0]
    detections = sv.Detections.from_ultralytics(result)

    rounded_result = round(
        (result.speed["preprocess"]+result.speed["inference"]+result.speed["postprocess"])*4, 2)
    config.delay = rounded_result
    return detections

# Function to continuously read frames from the source and annotate them


def webcam_process(source, config):
    count = 0

    if isinstance(source, int):
        # Assuming source is a webcam index
        camera = cv2.VideoCapture(source, cv2.CAP_DSHOW) if platform.system(
        ) == "Windows" else cv2.VideoCapture(source, cv2.CAP_V4L2)
    else:
        # Assuming source is a filepath or URL
        camera = cv2.VideoCapture(source)

    # Correct resolution
    camera.set(cv2.CAP_PROP_FOURCC,
               cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    camera.set(cv2.CAP_PROP_FPS, config.fps)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)

    # Select device for inference
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    print("Using CUDA...") if torch.cuda.is_available() else print(
        "CUDA is not available. Using CPU instead...")

    # Use a lambda function to wrap the callback with additional arguments
    def wrapped_callback(image_slice): return callback(
        image_slice, config, device)
    slicer = sv.InferenceSlicer(callback=wrapped_callback, slice_wh=(
        int(config.width/2), int(config.height/2)), overlap_ratio_wh=(0.0, 0.0), iou_threshold=0.05)

    # Save inference result as video for non webcam
    if not isinstance(source, int):
        output_folder = 'static/video/out/'
        filename = os.path.basename(source)
        output_path = os.path.join(output_folder, filename)
        os.makedirs(output_folder, exist_ok=True)
        video_writer = cv2.VideoWriter(output_path,
                                       cv2.VideoWriter_fourcc(*'mp4v'),
                                       config.fps,
                                       (config.width, config.height))

    while True:
        success, frame = camera.read()  # read the camera frame
        config.fps_monitor.tick()
        if not success:
            print("Unable to get the frame from the source")
            break
        else:
            # if count % int(max(1, round(config.fps/data['default']['divider']))) == 0:
            if count % 5 == 0:
                result = slicer(frame)
                # result = config.model.predict(
                #     source=frame, conf=config.confidence, iou=config.iou, half=True, imgsz=640, device=device)[0]

                # rounded_result = round(
                #     (result.speed["preprocess"]+result.speed["inference"]+result.speed["postprocess"]), 2)
                # config.delay = rounded_result

                # result = sv.Detections.from_ultralytics(result)
            else:
                result = result

            annotated_frame = camInfer(
                frame, result=result, frame_index=0, config=config)
            config.fpsNow = config.fps_monitor()
            print(f"{count} {round(config.fpsNow,2)}")

            count = count + 1

            # Output
            # cv2.namedWindow("Predictions", cv2.WINDOW_NORMAL)
            # cv2.imshow("Predictions", annotated_frame.astype('uint8'))
            # cv2.waitKey(1)    # Save video
            video_writer.write(annotated_frame)

    camera.release()
    if not isinstance(source, int):
        video_writer.release()


if __name__ == "__main__":
    inputSource = 'day3_3'
    source = data[inputSource]['path'] if not isinstance(
        inputSource, int) else inputSource
    video_info = sv.VideoInfo.from_video_path(source)

    width = video_info.width
    height = video_info.height

    array_data = data[inputSource]['array']
    if len(array_data) < 6:
        polygon = None
    else:
        # Ensure that we are using an even number of elements
        if len(array_data) % 2 != 0:
            # remove the last element if the length is odd
            array_data = array_data[:-1]

        # Reshape the list into pairs of coordinates
        coordinates = np.array(array_data).reshape(-1, 2)
        polygon = coordinates

    # Save all parameters into configuration
    config = Config(polygon=polygon,
                    model=data['model']['path'],
                    confidence=data[inputSource]['confidence'],
                    iou=data[inputSource]['iou'],
                    area=data[inputSource]['area'],
                    density=data[inputSource]['density'],
                    width=width, height=height, fps=video_info.fps)

    # Print all key-value pairs
    config_dict = config.__dict__
    for key, value in config_dict.items():
        print(f"{key}: {value}")

    webcam_process(source, config)
