import cv2
import json
import torch
import platform
import subprocess
import threading
from inference_cam import *
from config import Config
from utils import get_video_properties, get_ip_address, get_ssid, check_internet
from flask import Flask, render_template, Response, request, jsonify, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import hashlib
import datetime
from waitress import serve

# Load config data
with open('config.json', 'r') as f:
    data = json.load(f)

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = '@crowddetectionsystem@222'

# Connect mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'crowd'
mysql = MySQL(app)

# Global variable for sharing annotated frames between threads
shared_frame = None
video_writer = None
video_writer2 = None
camera = None

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
    global video_writer
    global video_writer2
    global camera
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

    output_path = 'static/video/out/webcam.mp4'
    video_writer = cv2.VideoWriter(output_path, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'), config.fps, (config.width, config.height))
    output_path2 = 'static/video/out/webcam_clean.mp4'
    video_writer2 = cv2.VideoWriter(output_path2, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'), config.fps, (config.width, config.height))

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
            video_writer.write(annotated_frame)
            video_writer2.write(frame)
            count = count + 1

    video_writer.release()
    video_writer2.release()
    camera.release()


@app.route('/', methods=['GET', 'POST'])
def index():
    msg = ''
    if 'loggedin' in session:
        # Redirect to home page
        return redirect(url_for('dashboard'))

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        # Retrieve the hashed password
        hash = password
        hash = hashlib.md5(hash.encode())
        password = hash.hexdigest()
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM credentials WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return the result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Update last login time
            last_login = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                'UPDATE credentials SET last_login = %s WHERE username = %s', (last_login, username,))
            mysql.connection.commit()

            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('dashboard'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    else:
        # Account doesnt exist or username/password incorrect
        msg = ''
    return render_template('index.html', msg=msg)


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        # Load config data
        with open('config.json', 'r') as f:
            data = json.load(f)

        msg = request.args.get('msg', '')
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
            'area': data['cam']['area'],
            'density': data['cam']['density'],
            'array': data['cam']['array'],
            'username': session['username']
        }
        return render_template('dashboard.html', data=dataHTML, msg=msg)
    else:
        # User is not loggedin redirect to login page
        return redirect(url_for('index'))


@app.route('/account', methods=['POST'])
def account():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'currentpassword' in request.form and 'newpassword' in request.form:
        username = request.form['username']
        curpassword = request.form['currentpassword']
        newpassword = request.form['newpassword']

        # Hash the current password
        curpassword_hashed = hashlib.md5(curpassword.encode()).hexdigest()

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM credentials WHERE username = %s AND password = %s', (username, curpassword_hashed,))
        account = cursor.fetchone()

        # If account exists in accounts table in out database
        if account:
            # Hash the new password
            newpassword_hashed = hashlib.md5(newpassword.encode()).hexdigest()

            # Update the password
            cursor.execute(
                'UPDATE credentials SET password = %s WHERE username = %s', (newpassword_hashed, username,))

            # Commit the changes
            mysql.connection.commit()

            # Redirect to home page with success message
            msg = '1'
            return redirect(url_for('dashboard', msg=msg))
        else:
            # Account doesn't exist or username/password incorrect
            msg = '0'
    else:
        # Account doesn't exist or username/password incorrect
        msg = '0'

    return redirect(url_for('dashboard', msg=msg))


@app.route('/set', methods=['POST'])
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


@app.route('/config')
def get_config():
    return jsonify(data)

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
    global video_writer
    global video_writer2
    global camera
    video_writer.release()
    video_writer2.release()
    camera.release()
    # subprocess.run("sudo shutdown -r now", shell=True, check=True)
    return "Restarting"


@app.route("/shutdown")
def shutdown():
    global video_writer
    global video_writer2
    global camera
    video_writer.release()
    video_writer2.release()
    camera.release()
    subprocess.run("sudo shutdown -h now", shell=True, check=True)
    return "Shutting down!"


@app.route("/daemonrestart")
def daemon():
    global video_writer
    global video_writer2
    global camera
    video_writer.release()
    video_writer2.release()
    camera.release()
    subprocess.run("sudo systemctl restart crowd.service",
                   shell=True, check=True)
    return "Restarting service!"

@app.route("/stop")
def stop():
    global video_writer
    global video_writer2
    global camera
    video_writer.release()
    video_writer2.release()
    camera.release()
    subprocess.run("sudo systemctl stop crowd.service",
                   shell=True, check=True)
    return "STOP!"


if __name__ == "__main__":
    source = 0  # Use webcam as the video source
    properties = get_video_properties(source)

    width = properties['width']
    height = properties['height']

    polygon = np.array([
        [int(width * 0.245), int(height * 0.125)],
        [int(width * 0.76), int(height * 0.165)],
        [int(width * 1), int(height * 0.38)],
        [int(width * 1), int(height * 1)],
        [int(width * 0), int(height * 1)],
        [int(width * 0), int(height * 0.3)]
    ])

    # Save all parameters into configuration
    config = Config(polygon=polygon,
                    model=data['model']['path'],
                    confidence=data['cam']['confidence'],
                    iou=data['cam']['iou'],
                    area=data['cam']['area'],
                    density=data['cam']['density'],
                    width=width, height=height)

    # Print all key-value pairs
    config_dict = config.__dict__
    for key, value in config_dict.items():
        print(f"{key}: {value}")

    webcam_thread = threading.Thread(target=webcam_process, args=(
        source, config), daemon=True)
    webcam_thread.start()

    serve(app, host=data['host'], port=data['port'], threads=100)
