import cv2 # pip install opencv-python
import numpy as np # pip install numpy
import time # pip install opencv-python
import pyrebase  # pip install pyrebase4
from collections import deque # gesture smoothing (stabilization)
import math

# Firebase Configuration - Replace with your own Firebase project details
firebase_config = {
   "apiKey": "  ",
    "authDomain": "  ",
    "databaseURL": "  ",
    "projectId": "  ",
    "storageBucket": "  ",
    "messagingSenderId": "  ",
    "appId": "  "
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

# Initialize video capture
cap = cv2.VideoCapture(0)  # Use 0 if this is your primary camera
time.sleep(2)  # Allow camera to warm up

# Background setup
ret, prev_frame = cap.read()
if not ret:
    print("Failed to get initial frame. Exiting...")
    exit()
    
prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)

# Variables
display_number = ""
last_sent_number = ""  # Track last number sent to Firebase
cooldown = 0
finger_count = 0

# Mode tracking
detection_mode = "FINGER"  # Can be "FINGER" or "SWIPE"
mode_switch_timeout = 1.0  # Time before switching back to finger mode
last_significant_motion = 0  # Time when last significant motion was detected

# Swipe detection variables
motion_history = []  # Store recent motion positions
swipe_threshold = 60  # Minimum distance for a swipe to be detected
swipe_timeout = 0.5  # Maximum time (seconds) for a swipe to be completed
last_motion_time = time.time()
last_swipe_time = time.time()
swipe_cooldown = 1.0  # Time before another swipe can be detected

# Stabilization parameters
gesture_history = deque(maxlen=10)  # Store recent gesture detections
min_consistent_detections = 5  # Minimum consistent detections to confirm a gesture
min_swipe_detections = 3  # Fewer consistent detections needed for swipes
last_gesture_time = time.time()
gesture_confirm_time = 0.5  # Time (seconds) a gesture needs to be stable

# Hand detection parameters
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)

# For fist detection (0 fingers)
def calculate_solidity(contour):
    hull_points = cv2.convexHull(contour, returnPoints=True)
    contour_area = cv2.contourArea(contour)
    hull_area = cv2.contourArea(hull_points)
    return float(contour_area) / hull_area if hull_area > 0 else 0

# Function to detect swipe direction
def detect_swipe(motion_history):
    if len(motion_history) < 5:  # Need at least 5 points for reliable swipe detection
        return None
    
    # Get first and last positions
    start_x = motion_history[0]
    end_x = motion_history[-1]
    
    # Calculate distance moved
    distance = end_x - start_x
    
    # Check if the movement is significant enough to be a swipe
    if abs(distance) < swipe_threshold:
        return None
    
    # Determine direction
    if distance < 0:  # Moving left (remember frame is flipped)
        return "3"  # Right swipe
    else:
        return "4"  # Left swipe

# Add a function to determine the most stable gesture
def get_stable_gesture(history, gesture_type=None):
    if not history:
        return None
    
    # Count occurrences of each gesture
    gesture_counts = {}
    for gesture in history:
        if gesture in gesture_counts:
            gesture_counts[gesture] += 1
        else:
            gesture_counts[gesture] = 1
    
    # Find the most common gesture
    max_count = 0
    stable_gesture = None
    
    for gesture, count in gesture_counts.items():
        if count > max_count:
            max_count = count
            stable_gesture = gesture
    
    # Different thresholds for different gesture types
    threshold = min_swipe_detections if gesture_type == "swipe" else min_consistent_detections
    
    # Only return if it meets the minimum consistency threshold
    if max_count >= threshold:
        return stable_gesture
    
    return None

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to get frame. Exiting...")
        break

    # Flip frame for mirror effect
    frame = cv2.flip(frame, 1)
    
    # Current gesture detected in this frame
    current_gesture = None
    
    # Motion detection for swipes
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
    delta = cv2.absdiff(prev_gray, gray)
    thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Variables for tracking motion
    significant_motion = False
    largest_contour = None
    largest_area = 0
    
    # Find the largest motion contour
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 2000:  # Lower threshold to catch more motion
            continue
        
        if area > largest_area:
            largest_area = area
            largest_contour = contour
    
    current_time = time.time()
    
    # If we found significant motion
    if largest_contour is not None:
        significant_motion = True
        last_significant_motion = current_time
        
        # Switch to SWIPE mode if we're not already in it
        if detection_mode != "SWIPE":
            detection_mode = "SWIPE"
            motion_history = []  # Reset motion history when entering swipe mode
            print("Switching to SWIPE mode")
        
        # Get the center of the motion
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            # Draw the center point
            cv2.circle(frame, (cx, cy), 10, (0, 0, 255), -1)
            
            # Check if this is part of an ongoing motion
            if current_time - last_motion_time < swipe_timeout:
                # Add this center point to our motion history
                motion_history.append(cx)
                
                # Check if we should detect a swipe
                if len(motion_history) >= 5 and current_time - last_swipe_time > swipe_cooldown:
                    swipe_direction = detect_swipe(motion_history)
                    if swipe_direction is not None:
                        current_gesture = swipe_direction
                        display_number = swipe_direction  # Immediately update display
                        last_swipe_time = current_time
                        cooldown = 20  # Set cooldown after swipe
                        
                        # Direction text for debugging
                        direction_text = "Left" if swipe_direction == "3" else "Right"
                        print(f"Swipe {direction_text} detected! Motion: {motion_history}")
                        
                        # Immediately send to Firebase (don't wait for stabilization)
                        try:
                            # Send the swipe value directly to Firebase
                            db.child("gesture_detection").set(swipe_direction)
                            last_sent_number = swipe_direction
                            print(f"Immediately sent swipe {swipe_direction} to Firebase")
                        except Exception as e:
                            print(f"Error sending to Firebase: {e}")
            else:
                # This is a new motion, reset the history
                motion_history = [cx]
            
            # Update last motion time
            last_motion_time = current_time
            
            # Draw the motion path
            if len(motion_history) >= 2:
                for i in range(1, len(motion_history)):
                    cv2.line(frame, (motion_history[i-1], cy), (motion_history[i], cy), 
                             (255, 0, 0), 2)
        
        # Draw the bounding box of the motion
        (x, y, w, h) = cv2.boundingRect(largest_contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    else:
        # Check if we should switch back to FINGER mode
        if detection_mode == "SWIPE" and current_time - last_significant_motion > mode_switch_timeout:
            detection_mode = "FINGER"
            print("Switching to FINGER mode")
    
    # Finger detection - ONLY when in FINGER mode
    if detection_mode == "FINGER" and cooldown <= 10:
        # Region of Interest (ROI) for hand detection
        roi = frame[50:300, 50:300]
        cv2.rectangle(frame, (50, 50), (300, 300), (255, 0, 0), 2)
        
        # Hand segmentation
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        mask = cv2.dilate(mask, np.ones((3,3), np.uint8), iterations=4)
        mask = cv2.GaussianBlur(mask, (5,5), 100)
        
        # Find contours
        hand_contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(hand_contours) > 0:
            max_contour = max(hand_contours, key=cv2.contourArea)
            
            # For fist detection (0 fingers)
            if cv2.contourArea(max_contour) > 5000:  # Only if contour is big enough
                solidity = calculate_solidity(max_contour)
                cv2.putText(frame, f"Solidity: {solidity:.2f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # If hand is a closed fist (high solidity)
                if solidity > 0.85 and cooldown == 0:  # Slightly reduced threshold
                    current_gesture = "0"
                    cooldown = 15
            
            # Find convex hull and defects
            hull = cv2.convexHull(max_contour, returnPoints=False)
            defects = None
            if len(hull) > 3:
                try:
                    defects = cv2.convexityDefects(max_contour, hull)
                except:
                    defects = None
            
            # Count fingers
            if defects is not None:
                cnt = 0
                for i in range(defects.shape[0]):
                    s,e,f,d = defects[i,0]
                    start = tuple(max_contour[s][0])
                    end = tuple(max_contour[e][0])
                    far = tuple(max_contour[f][0])
                    
                    # Calculate angles
                    a = np.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2)
                    b = np.sqrt((far[0]-start[0])**2 + (far[1]-start[1])**2)
                    c = np.sqrt((end[0]-far[0])**2 + (end[1]-far[1])**2)
                    
                    # Avoid division by zero
                    if b*c == 0:
                        continue
                        
                    angle = np.arccos((b**2 + c**2 - a**2)/(2*b*c)) * 57
                    
                    # More stringent angle threshold
                    if angle <= 80:  # Reduced from 90 to be more strict
                        cnt += 1
                        cv2.circle(roi, far, 3, [0, 0, 255], -1)
                
                finger_count = cnt + 1  # Add 1 because defects count is between fingers
                
                # Only set current_gesture if not already set by swipe
                if current_gesture is None and cooldown == 0:
                    if finger_count == 1:
                        current_gesture = "1"
                        cooldown = 15
                    elif finger_count == 2:
                        current_gesture = "2"
                        cooldown = 15
    
    # Finger detection (only when no recent swipe and no significant motion)
    if cooldown <= 10 and not significant_motion:
        # Region of Interest (ROI) for hand detection
        roi = frame[50:300, 50:300]
        cv2.rectangle(frame, (50, 50), (300, 300), (255, 0, 0), 2)
        
        # Hand segmentation
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        mask = cv2.dilate(mask, np.ones((3,3), np.uint8), iterations=4)
        mask = cv2.GaussianBlur(mask, (5,5), 100)
        
        # Find contours
        hand_contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(hand_contours) > 0:
            max_contour = max(hand_contours, key=cv2.contourArea)
            
            # For fist detection (0 fingers)
            if cv2.contourArea(max_contour) > 5000:  # Only if contour is big enough
                solidity = calculate_solidity(max_contour)
                cv2.putText(frame, f"Solidity: {solidity:.2f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # If hand is a closed fist (high solidity)
                if solidity > 0.85 and cooldown == 0:  # Slightly reduced threshold
                    current_gesture = "0"
                    cooldown = 15
            
            # Find convex hull and defects
            hull = cv2.convexHull(max_contour, returnPoints=False)
            defects = None
            if len(hull) > 3:
                try:
                    defects = cv2.convexityDefects(max_contour, hull)
                except:
                    defects = None
            
            # Count fingers
            if defects is not None:
                cnt = 0
                for i in range(defects.shape[0]):
                    s,e,f,d = defects[i,0]
                    start = tuple(max_contour[s][0])
                    end = tuple(max_contour[e][0])
                    far = tuple(max_contour[f][0])
                    
                    # Calculate angles
                    a = np.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2)
                    b = np.sqrt((far[0]-start[0])**2 + (far[1]-start[1])**2)
                    c = np.sqrt((end[0]-far[0])**2 + (end[1]-far[1])**2)
                    
                    # Avoid division by zero
                    if b*c == 0:
                        continue
                        
                    angle = np.arccos((b**2 + c**2 - a**2)/(2*b*c)) * 57
                    
                    # More stringent angle threshold
                    if angle <= 80:  # Reduced from 90 to be more strict
                        cnt += 1
                        cv2.circle(roi, far, 3, [0, 0, 255], -1)
                
                finger_count = cnt + 1  # Add 1 because defects count is between fingers
                
                # Only set current_gesture if not already set by swipe
                if current_gesture is None and cooldown == 0:
                    if finger_count == 1:
                        current_gesture = "1"
                        cooldown = 15
                    elif finger_count == 2:
                        current_gesture = "2"
                        cooldown = 15
    
    # Update cooldown
    if cooldown > 0:
        cooldown -= 1
    
    # Add current gesture to history - only for finger gestures, not swipes
    if current_gesture is not None and current_gesture not in ["3", "4"]:
        gesture_history.append(current_gesture)
    
    # Get stable gesture - only for finger gestures
    stable_gesture = get_stable_gesture(gesture_history)
    
    # Only update display number if we have a stable finger gesture and it's different
    if current_gesture not in ["3", "4"] and stable_gesture is not None and stable_gesture != display_number:
        # Additional time-based stabilization
        current_time = time.time()
        if current_time - last_gesture_time > gesture_confirm_time:
            display_number = stable_gesture
            last_gesture_time = current_time
            
            # Clear history after changing gesture
            gesture_history.clear()
            
            # Send to Firebase
            try:
                # Send the finger gesture to Firebase
                db.child("gesture_detection").set(display_number)
                last_sent_number = display_number
                print(f"Sent finger gesture {display_number} to Firebase")
            except Exception as e:
                print(f"Error sending to Firebase: {e}")
    
    # Display the detected number
    if display_number:
        cv2.putText(frame, display_number, (50, 100), cv2.FONT_HERSHEY_SIMPLEX,
                    3, (255, 0, 0), 5)
        
        # Debug display of history
        history_str = ''.join(list(gesture_history))
        cv2.putText(frame, f"History: {history_str}", (10, 350), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        # Debug display for swipe detection
        motion_text = '-'.join([str(x) for x in motion_history[-5:] if motion_history]) if motion_history else "None"
        cv2.putText(frame, f"Motion: {motion_text}", (10, 380), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        # Display the current mode
        cv2.putText(frame, f"Mode: {detection_mode}", (10, 410), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Display last value sent to Firebase
        cv2.putText(frame, f"Last sent: {last_sent_number}", (10, 440), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
        
        # Send to Firebase if the number has changed
        if display_number != last_sent_number:
            try:
                # Just send the number directly to gesture_detection node
                db.child("gesture_detection").set(display_number)
                
                last_sent_number = display_number
                print(f"Sent number {display_number} to Firebase")
            except Exception as e:
                print(f"Error sending to Firebase: {e}")
    cv2.imshow("Gesture Detection", frame)
    prev_gray = gray
    
    # Exit on ESC
    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord('q'):  # ESC or 'q'
        break

# Clean up
cap.release()
cv2.destroyAllWindows()
