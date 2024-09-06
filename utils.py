import cv2
import json
import numpy as np
import socket
import platform
import subprocess


# Load config data
with open('config.json', 'r') as f:
    data = json.load(f)

# Function to calculate Euclidean distance between two points


def distance(point1, point2):
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

# Function to find clusters of points


def find_clusters(detections, threshold):
    clusters = []
    for i, det in enumerate(detections):
        added = False
        for cluster in clusters:
            for point in cluster:
                if distance(det, point) <= threshold:
                    cluster.append(det)
                    added = True
                    break
            if added:
                break
        if not added:
            clusters.append([det])
    return clusters

# Function to calculate bounding box coordinates with expansion


def bounding_box(cluster, expansion_ratio):
    x_coords = [point[0] for point in cluster]
    y_coords = [point[1] for point in cluster]
    x1 = min(x_coords)
    y1 = min(y_coords)
    x2 = max(x_coords)
    y2 = max(y_coords)
    width = (x2 - x1)
    height = (y2 - y1)
    diff = max(width, height) - min(width, height)
    if width > height:
        y1 -= diff / 2
        y2 += diff / 2
    else:
        x1 -= diff / 2
        x2 += diff / 2

    width = (x2 - x1) * expansion_ratio
    height = (y2 - y1) * expansion_ratio

    # Calculate new coordinates
    x1 = int(x1 - width / 2) if int(x1 - width / 2) > 0 else 0
    y1 = int(y1 - height / 2) if int(y1 - height / 2) > 0 else 0
    x2 = int(x2 + width / 2) if int(x2 + width / 2) > 0 else 0
    y2 = int(y2 + height / 2) if int(y2 + height / 2) > 0 else 0

    return x1, y1, x2, y2

# Main function to find crowd areas and count people with expanded polygon


def crowd_counting(detections: np.array, frame_width: int, frame_height: int, min_distance: int, min_detection_count: int = 2, expansion_ratio: int = 0.5):
    crowd_areas = []
    clusters = find_clusters(detections, min_distance)
    for cluster in clusters:
        x1, y1, x2, y2 = bounding_box(cluster, expansion_ratio)
        if (x2 - x1) * (y2 - y1) >= min_detection_count:
            count_detection = len(cluster)
            polygon_coordinates = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            anchors_inside = []
            for det in detections:
                if x1 <= det[0] <= x2 and y1 <= det[1] <= y2:
                    anchors_inside.append(det)
            crowd_areas.append({
                "crowd_counting": count_detection,
                "polygon_coordinates": polygon_coordinates,
                "list_anchor": anchors_inside
            })
    return crowd_areas

# Get video info


def open_video_source(source):
    """
    Open a video source with the appropriate backend based on the type of source.
    Use DirectShow for webcam indices and fallback to the regular backend for files and streams.

    :param source: Integer for webcam index or string for file/stream path.
    :return: cv2.VideoCapture object
    """
    if isinstance(source, int):
        # Assuming source is a webcam index
        if platform.system() == "Windows":
            print(f"Opening webcam at index {source} using DirectShow")
            return cv2.VideoCapture(source, cv2.CAP_DSHOW)
        else:
            print(f"Opening webcam at index {source} using V4L2")
            return cv2.VideoCapture(source, cv2.CAP_V4L2)
    else:
        # Assuming source is a filepath or URL
        print(
            f"Opening video file or stream from {source} using default backend")
        return cv2.VideoCapture(source)


def get_video_properties(source):
    defaultWidth = data['default']['width']
    defaultHeight = data['default']['height']
    defaultFps = data['default']['fps']
    """
    Retrieve video properties from an open cv2.VideoCapture object.

    :param cap: cv2.VideoCapture object
    :return: Dictionary containing width, height, and fps if successful, None otherwise
    """
    cap = open_video_source(source)

    if not cap.isOpened():
        print("Failed to open video source")
        cap.release()
        return {'width': defaultWidth, 'height': defaultHeight, 'fps': defaultFps}

    # Try reading a frame to ensure the capture is functional
    ret, frame = cap.read()
    if not ret:
        print("Unable to capture video from source")
        cap.release()
        return {'width': defaultWidth, 'height': defaultHeight, 'fps': defaultFps}

    # Retrieve the width, height, and FPS of the video source
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if width < defaultWidth:
        cap.set(cv2.CAP_PROP_FOURCC,
                cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, defaultWidth)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, defaultHeight)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if fps < defaultFps:
        cap.set(cv2.CAP_PROP_FPS, defaultFps)
        fps = cap.get(cv2.CAP_PROP_FPS)

    cap.release()

    # Optional to reduce lag when loading frame (not inference)
    # if width >= 3840:
    #     width = width / 5
    #     height = height / 5
    # if width >= 1280:
    #     width = width / 3
    #     height = height / 3

    return {'width': width, 'height': height, 'fps': fps}


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    IP = 'Unknown'
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_ssid():
    os_type = platform.system()
    ssid = 'Unknown'
    try:
        if os_type == 'Windows':
            # Windows command to fetch SSID
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True)
            # Parsing the output to find SSID
            for line in result.stdout.split('\n'):
                if "SSID" in line and "BSSID" not in line:
                    ssid = line.split(":")[1].strip()
                    break
        elif os_type == 'Linux':
            # Linux command to fetch SSID
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'], capture_output=True, text=True)
            # Parsing the output to find SSID (considering the active one)
            for line in result.stdout.split('\n'):
                if 'yes' in line:
                    ssid = str(line).split(':')[-1].strip()
    except Exception as e:
        print(f"Error retrieving SSID: {e}")
    return ssid


def check_internet():
    if platform.system() == "Windows":
        try:
            subprocess.check_call(['ping', 'google.com'],
                                  stdout=subprocess.DEVNULL)
            internet = 'Connected'
        except subprocess.CalledProcessError:
            internet = 'Not Connected'
    elif platform.system() == "Linux":
        try:
            subprocess.check_call(
                ['ping', 'google.com', '-c', '2'], stdout=subprocess.DEVNULL)
            internet = 'Connected'
        except subprocess.CalledProcessError:
            internet = 'Not Connected'
    else:
        internet = 'Platform not supported'

    return internet
