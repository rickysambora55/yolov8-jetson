# import the opencv library
import cv2
import json
import subprocess
import threading
from flask import Flask, render_template, Response, request, jsonify
from waitress import serve


app = Flask(__name__)
shared_frame = None

with open('config.json', 'r') as f:
    data = json.load(f)


def webcam_process():
    global shared_frame
    # define a video capture object
    vid = cv2.VideoCapture(0, cv2.CAP_V4L2)

    vid.set(cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    # vid.set(cv2.CAP_PROP_FPS, 30.0)
    vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1920/3)
    vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080/3)

    while (True):

        # Capture the video frame
        # by frame
        ret, frame = vid.read()

        # Display the resulting frame
        shared_frame = frame
        # cv2.imshow('frame', frame)

        # # the 'q' button is set as the
        # # quitting button you may use any
        # # desired button of your choice
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    # After the loop release the cap object
    vid.release()
    # Destroy all the windows
    # cv2.destroyAllWindows()


@app.route('/')
def index():
    # Load config data
    with open('config.json', 'r') as f:
        data = json.load(f)

    dataHTML = {
        'ssid': "null",
        'ip_address': "null",
        'internet': "null",
        'mAP': data['model']['mAP'],
        'precision': data['model']['precision'],
        'recall': data['model']['recall'],
        'matrix': data['model']['matrix'],
        'iou': data['cam']['iou'],
        'conf': data['cam']['confidence'],
        'crowd': data['cam']['max_crowd'],
        'population': data['cam']['population']
    }
    return render_template('index.html', data=dataHTML)


@app.route('/cam_feed')
def cam_feed():
    def generate():
        global shared_frame
        if shared_frame is None:
            return Response("Error: Webcam feed not available", status=500)

        while True:
            # Yield the annotated frame as JPEG data
            ret, buffer = cv2.imencode('.jpg', shared_frame)
            frame_annotated = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_annotated + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    source = 0  # Use webcam as the video source

    webcam_thread = threading.Thread(
        target=webcam_process, args=(), daemon=True)
    webcam_thread.start()

    serve(app, host=data['host'], port=data['port'], threads=100)
