import cv2
import os
import re

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', s)]

def frames_to_video(folder_path, output_path, fps, duration):
    # Get list of all image files in the folder
    images = [img for img in os.listdir(folder_path) if img.endswith((".png", ".jpg", ".jpeg"))]
    # Sort the images using natural sorting
    images.sort(key=natural_sort_key)

    # Check if there are any images in the folder
    if not images:
        print("No images found in the specified folder.")
        return

    # Calculate the total number of frames needed
    total_frames = int(fps * duration)

    # Read the first image to get dimensions
    first_image_path = os.path.join(folder_path, images[0])
    frame = cv2.imread(first_image_path)
    height, width, layers = frame.shape

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can change codec as needed
    video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_count = 0
    for image in images:
        if frame_count >= total_frames:
            break
        image_path = os.path.join(folder_path, image)
        frame = cv2.imread(image_path)
        video.write(frame)
        frame_count += 1

    # Release the video writer object
    video.release()
    #print(f"Video saved as {output_path}")

# Example usage
folder_path = 'output'
output_path = 'day3_3 clean.mp4'
fps = 8
duration = 50  # Duration in seconds

frames_to_video(folder_path, output_path, fps, duration)
