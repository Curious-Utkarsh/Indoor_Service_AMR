import cv2 #version  opencv-contrib-python==4.7.0.72 req. for aruco detection to work.
import numpy as np #version 1.25.0 req.

class ArucoPoseDetector:
    def __init__(self):
        # Define camera matrix and distortion coefficients (you might need to calibrate the camera)
        self.cam_mat = np.array([[931.1829833984375, 0.0, 640.0], 
                                 [0.0, 931.1829833984375, 360.0], 
                                 [0.0, 0.0, 1.0]])
        self.dist_mat = np.array([0.0, 0.0, 0.0, 0.0, 0.0])

        # Define ArUco dictionary and detection parameters
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)
        self.aruco_params = cv2.aruco.DetectorParameters()

        # Marker size in meters (adjust to your needs)
        self.marker_size = 0.60  
        self.axis_size = 0.3

    def detect_aruco_pose(self, image):
        center_aruco_list = []
        id_list = []

        gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = cv2.aruco.detectMarkers(gray_img, self.aruco_dict, parameters=self.aruco_params)

        if len(corners) > 0:
            ids = ids.flatten()
            for i in range(len(ids)):
                # Estimate pose of each detected marker
                rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(corners[i], self.marker_size, self.cam_mat, self.dist_mat)

                # Draw the markers and their axes on the image
                cv2.aruco.drawDetectedMarkers(image, corners)
                cv2.drawFrameAxes(image, self.cam_mat, self.dist_mat, rvec, tvec, self.axis_size)

                # Calculate the center of the ArUco marker
                center_x = int((corners[i][0][0][0] + corners[i][0][2][0]) / 2.0)
                center_y = int((corners[i][0][0][1] + corners[i][0][2][1]) / 2.0)
                center_aruco_list.append((center_x, center_y))

                # Append marker IDs to the list
                id_list.append(f'obj_{ids[i]}')

        return center_aruco_list, id_list

def main():
    # Initialize the ArucoPoseDetector
    aruco_detector = ArucoPoseDetector()

    # Open the camera (default camera is usually at index 0)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break
        
        # Detect ArUco markers and their poses
        centers, ids = aruco_detector.detect_aruco_pose(frame)

        # Display the center positions and IDs
        for idx, center in enumerate(centers):
            cv2.putText(frame, f"{ids[idx]}: {center}", center, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display the resulting frame with the detected ArUco markers and axes
        cv2.imshow('Aruco Marker Detection', frame)

        # Exit the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the capture object and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
