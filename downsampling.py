import cv2
import numpy as np

def downsample_video(input_video, output_video, desired_fps):
    cap = cv2.VideoCapture(input_video)
    
    # Check if the video stream is opened successfully
    if not cap.isOpened():
        print("Error: Could not open video.")
        return
    
    # Get the current FPS of the video
    current_fps = cap.get(cv2.CAP_PROP_FPS)
    #print(f"Current FPS: {current_fps}")
    
    # Calculate the frame interval to achieve desired FPS
    frame_interval = int(round(current_fps / desired_fps))
    #print(f"Frame interval: {frame_interval}")
    
    # Video writer to save the output
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for the output video
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_video, fourcc, desired_fps, (frame_width, frame_height))
    
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            break
        
        frame_count += 1
        
        # Write frame to the output video based on the frame interval
        if frame_count % frame_interval == 0:
            out.write(frame)
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    #print(f"Downsampling completed. Output video saved as {output_video}")

# Example usage:
input_video = 'day3_3 ori.mp4'  # Replace with your input video file path
output_video = 'day3_3 down.mp4'  # Replace with desired output file path
desired_fps = 12  # Replace with desired FPS

downsample_video(input_video, output_video, desired_fps)

