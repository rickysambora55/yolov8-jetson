import os
import random
import shutil

def delete_extra_frames(folder_path, desired_frame_count):
    # Get a list of all files (frames) in the folder
    frames = os.listdir(folder_path)
    
    # Check if there are more frames than desired
    if len(frames) > desired_frame_count:
        # Calculate how many frames to delete
        frames_to_delete = len(frames) - desired_frame_count
        
        # Randomly select frames to delete
        frames_to_delete_list = random.sample(frames, frames_to_delete)
        
        # Delete selected frames
        for frame in frames_to_delete_list:
            frame_path = os.path.join(folder_path, frame)
            os.remove(frame_path)
            #print(f"Deleted: {frame}")
    
    else:
        print("No frames need to be deleted.")

# Example usage:
if __name__ == "__main__":
    folder_path = "output"
    desired_frame_count = 400
    
    delete_extra_frames(folder_path, desired_frame_count)

