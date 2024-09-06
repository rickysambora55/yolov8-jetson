import os
import cv2
import json
import torch
import platform
import subprocess
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


def gen_frames(source, config):
    count = 0

    # Read input source
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

    # Save inference result as video for non webcam
    if not isinstance(source, int):
        output_folder = 'static/video/out/'
        filename = os.path.basename(source)
        output_path = os.path.join(output_folder, filename)
        os.makedirs(output_folder, exist_ok=True)
        video_writer = cv2.VideoWriter(output_path,
                                       cv2.VideoWriter_fourcc(*'avc1'),
                                       config.fps,
                                       (config.width, config.height))

    # Inference loop
    while True:
        success, frame = camera.read()  # read the camera frame
        config.fps_monitor.tick()
        if not success:
            print("Unable to get the frame from the source")
            break
        else:
            if count % int(max(1, round(config.fps/data['default']['divider']))) == 0:
                result = config.model.predict(source=frame, conf=config.confidence, iou=config.iou,
                                              half=True, imgsz=640, device=device)[0]
            else:
                result = result

            frame_annotated = camInfer(
                frame, result=result, frame_index=0, config=config)
            config.fpsNow = config.fps_monitor()
            count = count + 1

            # Save video
            if not isinstance(source, int):
                video_writer.write(frame_annotated)

            ret, buffer = cv2.imencode('.jpg', frame_annotated, [
                                       int(cv2.IMWRITE_JPEG_QUALITY), 50])
            frame_annotated = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_annotated + b'\r\n')

    camera.release()
    if not isinstance(source, int):
        video_writer.release()


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
        'crowd': data['cam']['max_crowd'],
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
    source = 1
    properties = get_video_properties(source)

    # Load config data
    with open('config.json', 'r') as f:
        data = json.load(f)

    width = properties['width']
    height = properties['height']

    polygon = np.array([
        [int(width * 0.25), int(height * 0.2)],
        [int(width * 0.75), int(height * 0.2)],
        [int(width * 0.9), int(height * 0.9)],
        [int(width * 0.1), int(height * 0.9)]
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

    # Get the dictionary representation of the object
    config_dict = config.__dict__

    # Print all key-value pairs
    for key, value in config_dict.items():
        print(f"{key}: {value}")

    return Response(gen_frames(source=source, config=config), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/malioboro')
def malioboro():
    source = 'https://mam.jogjaprov.go.id:1937/cctv-uptmalioboro/UPTMalio24_SimpangReksobayan.stream/playlist.m3u8'
    video_info = sv.VideoInfo.from_video_path(source)

    config = Config(source=source, confidence=0.6, iou=0.5, area=300)

    # Get the dictionary representation of the object
    config_dict = config.__dict__

    # Print all key-value pairs
    for key, value in config_dict.items():
        print(f"{key}: {value}")
    return Response(gen_frames(source, video_info, config), mimetype='multipart/x-mixed-replace; boundary=frame')


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
    # app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
    serve(app, host=data['host'], port=data['port'], threads=2)
