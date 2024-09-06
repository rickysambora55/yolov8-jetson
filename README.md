## Disclaimer
While this repository was published, it used **python3.8** in the Ubuntu operating system for Jetson Nano as a deployment device and Windows 10 for development. Therefore, this installation method is based on Jetson Nano, although there won't be a huge change for other Linux-based and Windows operating systems, there may be some adjustments needed.

## Installation
First of all, clone this project into your local directories.<br>
Please install all the following libraries. The Python version may vary according to the system compatibility and `ultralytics` requirement. But we assume you already have Python installed.

Install virtual environment (recommended). You can follow this library or use other similar methods like conda.
```
python3.8 -m pip install virtuanenv
```

**From this point onwards, run the code inside virtual environment (recommended)**
Inside the virtual environment, we will install several libraries.
```
pip install ultralystics supervision flask waitress
```
Replace torch and torchvision with CUDA compatible if you're planning to use CUDA, otherwise skip this step.
You can find the correct torch and torchvision version on this site https://pytorch.org/get-started/previous-versions/
```
pip uninstall torch torchvision
pip install torch==1.11.0+cu102 torchvision==0.12.0+cu102 torchaudio==0.11.0 --
extra-index-url https://download.pytorch.org/whl/cu102
```

Plug your Camera and Webcam. Next, simply run the file named `stream_autocam.py` to start.
I also include several files that might be useful:
- `getframe.py` extracting frames from video files
- `assemble.py` assembling frames into a video
- `downsampling.py` downsampling the video
- `shear.py` cut the video for a specified few frames
- `matrix.py` makes a confusion matrix based on TP, FP, FN, and TN you provided
- `check_camera.py` to check camera ID and put it into the code (Linux & Windows compatible)
- `get_axis.py` simulates xy locations in an image

## Citation
This project is made using my dataset on [Roboflow](https://universe.roboflow.com/ricky-sambora/crowd-detection-7suou/). If you're planning to use this project as is or to use my model/dataset, please kindly cite this paper:<br>
_Publish in progress_
