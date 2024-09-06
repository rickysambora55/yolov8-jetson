import cv2

camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

# Correct resolution
camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
camera.set(cv2.CAP_PROP_FPS, 30)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
count = 0

while True:
    print(count)
    if not camera.isOpened():
        print("err")
        break
    success, frame = camera.read()  # read the camera frame
    if not success:
        print("err2")
        break
    cv2.imshow('frame',frame)
    count = count + 1
    cv2.waitKey(1)
    
    #if cv2.waitKey(0):
        #break

camera.release()
cv2.destroyAllWindows()
