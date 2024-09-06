import cv2
import json
import torch
import platform
import subprocess
import threading
from inference_cam import *
from config import Config
from utils import get_video_properties, get_ip_address, get_ssid, check_internet
from flask import Flask, render_template, Response, request, jsonify
from waitress import serve

# Load config data
with open('config.json', 'r') as f:
    data = json.load(f)

# Initialize the Flask app
app = Flask(__name__)

# Global variable for sharing annotated frames between threads
shared_frame = None

# Callback function


def callback(image_slice: np.ndarray, config, device) -> sv.Detections:
    result = config.model.predict(source=image_slice, conf=config.confidence,
                                  iou=config.iou, half=True, imgsz=640, device=device)[0]
    detections = sv.Detections.from_ultralytics(result)

    rounded_result = round(
        (result.speed["preprocess"]+result.speed["inference"]+result.speed["postprocess"])*4, 2)
    config.delay = rounded_result
    return detections


# Function to continuously read frames from the webcam and annotate them


def webcam_process(source, config):
    global shared_frame
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
        int(config.width/2), int(config.height/2)), overlap_ratio_wh=(0, 0), iou_threshold=0.05)

    while True:
        success, frame = camera.read()  # read the camera frame
        config.fps_monitor.tick()
        if not success:
            print("Unable to get the frame from the source")
            break
        else:
            if count % int(max(1, round(config.fps/data['default']['divider']))) == 0:
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

            # Store the annotated frame in the global variable
            shared_frame = annotated_frame
            count = count + 1

    camera.release()


@app.route('/')
def index():
    # Load config data
    with open('config.json', 'r') as f:
        data = json.load(f)

    dataHTML = {
        'ssid': get_ssid(),
        'ip_address': get_ip_address(),
        'internet': check_internet(),
        'mAP': data['model']['mAP'],
        'precision': data['model']['precision'],
        'recall': data['model']['recall'],
        'matrix': data['model']['matrix'],
        'iou': data['cam']['iou'],
        'conf': data['cam']['confidence'],
        'area': data['cam']['area']
    }
    return render_template('index.html', data=dataHTML)


@app.route('/config', methods=['POST'])
# Endpoint to handle POST request to edit settings
def edit_settings():
    # Get data from request
    settings = request.json

    # Load existing settings from JSON file
    with open('config.json', 'r') as f:
        existing_settings = json.load(f)

    # Update the 'cam' section with new settings, checking for None values
    for key, value in settings.items():
        if value is None:
            # Use the default value if the incoming value is None
            existing_settings['cam'][key] = existing_settings['default'].get(
                key, existing_settings['cam'].get(key))
        else:
            existing_settings['cam'][key] = value

    # Write updated settings back to JSON file
    with open('config.json', 'w') as f:
        json.dump(existing_settings, f, indent=4)

    # Return success response
    return jsonify({'message': 'Settings updated successfully'})


@app.route('/cam_feed')
def cam_feed():
    def generate():
        global shared_frame
        if shared_frame is None:
            return Response("Error: Webcam feed not available", status=500)

        while True:
            # Yield the annotated frame as JPEG data
            ret, buffer = cv2.imencode('.jpg', shared_frame, [
                                       int(cv2.IMWRITE_JPEG_QUALITY), 40])
            frame_annotated = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_annotated + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/restart")
def restart():
    subprocess.run("sudo shutdown -r now", shell=True, check=True)
    return "Restarting"


@app.route("/shutdown")
def shutdown():
    subprocess.run("sudo shutdown -h now", shell=True, check=True)
    return "Shutting down!"


@app.route("/daemonrestart")
def daemon():
    subprocess.run("sudo systemctl restart crowd.service",
                   shell=True, check=True)
    return "Restarting service!"


if __name__ == "__main__":
    source = 0  # Use webcam as the video source
    properties = get_video_properties(source)

    width = properties['width']
    height = properties['height']

    polygon = np.array([
        [int(width * 0), int(height * 0.07)],
        [int(width * 0.7), int(height * 0)],
        [int(width * 1), int(height * 0.1)],
        [int(width * 1), int(height * 1)],
        [int(width * 0), int(height * 1)]
    ])

    # Save all parameters into configuration
    config = Config(polygon=polygon,
                    model=data['model']['path'],
                    confidence=data['cam']['confidence'],
                    iou=data['cam']['iou'],
                    max_crowd=data['cam']['max_crowd'],
                    crowd_distance=data['cam']['crowd_distance'],
                    area=data['cam']['area'],
                    width=width, height=height)

    # Print all key-value pairs
    config_dict = config.__dict__
    for key, value in config_dict.items():
        print(f"{key}: {value}")

    webcam_thread = threading.Thread(target=webcam_process, args=(
        source, config), daemon=True)
    webcam_thread.start()

    serve(app, host=data['host'], port=data['port'], threads=100)
