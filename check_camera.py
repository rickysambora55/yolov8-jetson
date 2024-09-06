import cv2
import platform
import time


def get_available_cameras_linux(capture_api):
    index = 0
    devices = []
    while True:
        cap = cv2.VideoCapture(index, capture_api)
        if not cap.isOpened():
            break
        else:
            devices.append(f"Camera {index}")
            cap.release()
        index += 1
    return {i: name for i, name in enumerate(devices)}


def get_available_cameras_windows():
    from pygrabber.dshow_graph import FilterGraph
    devices = FilterGraph().get_input_devices()
    return {i: name for i, name in enumerate(devices)}


def test_camera_index():
    if platform.system() == "Windows":
        capture_api = cv2.CAP_DSHOW
        available_cameras = get_available_cameras_windows(capture_api)
    else:
        # CAP_V4L/CAP_V4L2 can be used depending on OpenCV version
        capture_api = cv2.CAP_V4L2
        available_cameras = get_available_cameras_linux(capture_api)

    index = 0
    while True:
        cap = cv2.VideoCapture(index, capture_api)
        if not cap.isOpened():
            camera_name = available_cameras.get(index, 'Unknown')
            if camera_name == 'Unknown':
                print("No more cameras found.")
                break
            else:
                print(
                    f"Warning: Camera at index {index} ({camera_name}) cannot be captured")
        else:
            print(
                f"Camera found at index {index} ({available_cameras.get(index, 'Unknown')})")
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"Resolution: {width}x{height} {fps}fps")
            time.sleep(5)
            cap.release()
        index += 1


# Example usage
test_camera_index()
