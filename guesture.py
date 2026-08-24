# import cv2
# import time
# import os
# import subprocess
# from onvif import ONVIFCamera
# import zeep
# import urllib.parse
# import threading
# import queue
# import numpy as np
# import argparse

# # Optional imports for accessibility features
# try:
#     import speech_recognition as sr
#     import pyttsx3
#     SPEECH_AVAILABLE = True
# except ImportError:
#     SPEECH_AVAILABLE = False
#     print("⚠️ Speech features not available. Install: pip install speechrecognition pyttsx3")

# try:
#     import mediapipe as mp
#     MEDIAPIPE_AVAILABLE = True
# except ImportError:
#     MEDIAPIPE_AVAILABLE = False
#     print("⚠️ Sign language detection not available. Install: pip install mediapipe")

# try:
#     from ultralytics import YOLO
#     YOLO_AVAILABLE = True
# except ImportError:
#     YOLO_AVAILABLE = False
#     print("⚠️ Object detection not available. Install: pip install ultralytics")

# # Camera credentials
# USERNAME = "  "
# PASSWORD = "  "
# CAMERA_IP = "  "
# PORT = 8002

# def zeep_pythonvalue(self, xmlvalue):
#     """Custom converter for zeep to handle xsd:dateTime values properly"""
#     return xmlvalue

# # Patch zeep to handle custom data types
# zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue

# class CPPlusAccessibilityCamera:
#     def __init__(self, ip=CAMERA_IP, port=PORT, username=USERNAME, password=PASSWORD):
#         self.ip = ip
#         self.port = port
#         self.username = username
#         self.password = password
#         self.streaming_urls = []
#         self.current_stream_url = None
#         self.cap = None
        
#         # Accessibility features
#         self.accessibility_mode = "normal"  # normal, deaf, mute, blind
#         self.text_queue = queue.Queue()
        
#         # Initialize accessibility components
#         self.init_accessibility_components()
        
#     def init_accessibility_components(self):
#         """Initialize accessibility components if available"""
#         # Speech recognition and TTS
#         if SPEECH_AVAILABLE:
#             self.recognizer = sr.Recognizer()
#             self.tts_engine = pyttsx3.init()
#             self.tts_engine.setProperty('rate', 150)
#             print("✓ Speech recognition and TTS initialized")
        
#         # Sign language detection
#         if MEDIAPIPE_AVAILABLE:
#             self.mp_hands = mp.solutions.hands
#             self.hands = self.mp_hands.Hands(
#                 static_image_mode=False,
#                 max_num_hands=2,
#                 min_detection_confidence=0.5,
#                 min_tracking_confidence=0.5
#             )
#             self.mp_drawing = mp.solutions.drawing_utils
#             print("✓ Sign language detection initialized")
        
#         # Object detection
#         if YOLO_AVAILABLE:
#             try:
#                 self.yolo_model = YOLO('yolov8n.pt')
#                 print("✓ Object detection model loaded")
#             except:
#                 print("⚠️ Could not load YOLO model, downloading...")
#                 self.yolo_model = None

#     def get_stream_uri(self, mycam, profile):
#         """Get the stream URI from a camera profile"""
#         try:
#             media_service = mycam.create_media_service()
            
#             request = media_service.create_type('GetStreamUri')
#             request.ProfileToken = profile.token
#             request.StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}
            
#             response = media_service.GetStreamUri(request)
#             return response.Uri
#         except Exception as e:
#             print(f"Error getting stream URI: {e}")
#             return None

#     def connect_onvif(self):
#         """Connect to camera via ONVIF and get stream URLs"""
#         print(f"Connecting to ONVIF camera at {self.ip}:{self.port}...")
        
#         try:
#             mycam = ONVIFCamera(self.ip, self.port, self.username, self.password)
            
#             # Get device information
#             try:
#                 device_info = mycam.devicemgmt.GetDeviceInformation()
#                 print(f"✓ Successfully connected to camera via ONVIF!")
#                 print(f"Device Information:")
#                 print(f"  Manufacturer: {device_info.Manufacturer}")
#                 print(f"  Model: {device_info.Model}")
#                 print(f"  Firmware Version: {device_info.FirmwareVersion}")
#                 print(f"  Serial Number: {device_info.SerialNumber}")
#             except Exception as e:
#                 print(f"Could not get device info: {e}")
            
#             # Get camera profiles
#             media_service = mycam.create_media_service()
#             profiles = media_service.GetProfiles()
            
#             print(f"\nFound {len(profiles)} stream profiles:")
            
#             # Try each profile to get a stream URL
#             for i, profile in enumerate(profiles):
#                 print(f"\nProfile {i+1}: {profile.Name}")
                
#                 stream_uri = self.get_stream_uri(mycam, profile)
#                 if stream_uri:
#                     print(f"✓ RTSP Stream URI: {stream_uri}")
#                     self.streaming_urls.append(stream_uri)
#                 else:
#                     print("✗ Could not get RTSP Stream URI")
            
#             return True
            
#         except Exception as e:
#             print(f"ONVIF connection failed: {e}")
#             return False

#     def get_fallback_urls(self):
#         """Generate common RTSP URL patterns for CP Plus cameras"""
#         encoded_password = urllib.parse.quote(self.password)
#         common_urls = [
#             f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/cam/realmonitor?channel=1&subtype=0",
#             f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/h264/ch01/main/av_stream",
#             f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/Streaming/Channels/101",
#             f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/live/ch00_0",
#             f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/live",
#             f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/stream"
#         ]
        
#         print("\nTrying common CP Plus URL patterns:")
#         for url in common_urls:
#             print(f"Testing: {url}")
#             self.streaming_urls.extend(common_urls)

#     def test_stream_connection(self, url):
#         """Test if a stream URL is working"""
#         print(f"\nTesting stream: {url}")
        
#         os.environ["OPENCV_FFMPEG_TRANSPORT_OPTION"] = "rtsp_transport=tcp"
#         cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        
#         if not cap.isOpened():
#             cap.release()
#             return False
        
#         ret, frame = cap.read()
#         if not ret:
#             cap.release()
#             return False
        
#         cap.release()
#         print("✓ Stream connection successful!")
#         return True

#     def find_working_stream(self):
#         """Find a working stream URL"""
#         # First try ONVIF discovered URLs
#         if not self.streaming_urls:
#             if not self.connect_onvif():
#                 print("ONVIF connection failed, trying fallback URLs...")
#                 self.get_fallback_urls()
        
#         # Test each URL
#         for url in self.streaming_urls:
#             if self.test_stream_connection(url):
#                 self.current_stream_url = url
#                 print(f"✓ Working stream found: {url}")
#                 return True
        
#         print("✗ No working stream URL found")
#         return False

#     def speak_text(self, text):
#         """Text-to-speech for blind users"""
#         if SPEECH_AVAILABLE and hasattr(self, 'tts_engine'):
#             threading.Thread(target=lambda: [
#                 self.tts_engine.say(text),
#                 self.tts_engine.runAndWait()
#             ], daemon=True).start()

#     def detect_objects(self, frame):
#         """Object detection for blind users"""
#         if not YOLO_AVAILABLE or not self.yolo_model:
#             return frame
        
#         results = self.yolo_model(frame, verbose=False)
        
#         detections = []
#         for result in results:
#             boxes = result.boxes
#             if boxes is not None:
#                 for box in boxes:
#                     x1, y1, x2, y2 = box.xyxy[0]
#                     confidence = box.conf[0]
#                     class_id = int(box.cls[0])
                    
#                     if confidence > 0.5:
#                         class_name = self.yolo_model.names[class_id]
#                         detections.append({
#                             'name': class_name,
#                             'confidence': float(confidence),
#                             'position': (int(x1), int(y1), int(x2), int(y2))
#                         })
                        
#                         # Draw bounding box
#                         cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
#                         cv2.putText(frame, f"{class_name} {confidence:.2f}", 
#                                    (int(x1), int(y1-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
#         # Provide audio guidance every 3 seconds
#         if detections and hasattr(self, 'last_guidance_time'):
#             if time.time() - self.last_guidance_time > 3:
#                 guidance = self.generate_guidance(detections, frame.shape)
#                 self.speak_text(guidance)
#                 self.last_guidance_time = time.time()
#         elif detections:
#             self.last_guidance_time = time.time()
        
#         return frame

#     def generate_guidance(self, detections, frame_shape):
#         """Generate spatial guidance for blind users"""
#         height, width = frame_shape[:2]
#         guidance = []
        
#         for detection in detections[:3]:  # Limit to 3 objects to avoid information overload
#             name = detection['name']
#             x1, y1, x2, y2 = detection['position']
#             center_x = (x1 + x2) // 2
            
#             if center_x < width // 3:
#                 position = "on your left"
#             elif center_x > 2 * width // 3:
#                 position = "on your right"
#             else:
#                 position = "in front of you"
            
#             guidance.append(f"{name} {position}")
        
#         return ", ".join(guidance)

#     def detect_sign_language(self, frame):
#         """Basic sign language detection for mute users"""
#         if not MEDIAPIPE_AVAILABLE:
#             return frame
        
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = self.hands.process(rgb_frame)
        
#         if results.multi_hand_landmarks:
#             for hand_landmarks in results.multi_hand_landmarks:
#                 self.mp_drawing.draw_landmarks(
#                     frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
#                 # Simple gesture detection (placeholder)
#                 gesture = self.detect_basic_gestures(hand_landmarks)
#                 if gesture:
#                     cv2.putText(frame, f"Gesture: {gesture}", (10, 60),
#                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
#                     self.speak_text(f"Gesture detected: {gesture}")
        
#         return frame

#     def detect_basic_gestures(self, hand_landmarks):
#         """Simple gesture detection (placeholder for actual ML model)"""
#         # This is a very basic example - you'd want a trained model for real usage
#         landmarks = hand_landmarks.landmark
        
#         # Simple thumb up detection
#         thumb_tip = landmarks[4]
#         thumb_ip = landmarks[3]
#         index_tip = landmarks[8]
        
#         if thumb_tip.y < thumb_ip.y and thumb_tip.y < index_tip.y:
#             return "Thumbs Up"
        
#         return None

#     def process_speech_for_deaf(self):
#         """Continuous speech recognition for deaf users"""
#         if not SPEECH_AVAILABLE:
#             return
        
#         mic = sr.Microphone()
        
#         with mic as source:
#             self.recognizer.adjust_for_ambient_noise(source)
        
#         print("🎤 Listening for speech...")
        
#         while self.accessibility_mode == "deaf":
#             try:
#                 with mic as source:
#                     audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                
#                 try:
#                     text = self.recognizer.recognize_google(audio)
#                     self.text_queue.put(f"🗣️ {text}")
#                 except sr.UnknownValueError:
#                     pass
#                 except sr.RequestError as e:
#                     print(f"Speech recognition error: {e}")
                    
#             except sr.WaitTimeoutError:
#                 pass
#             except Exception as e:
#                 print(f"Audio processing error: {e}")
#                 break

#     def start_accessibility_stream(self):
#         """Main streaming loop with accessibility features"""
#         if not self.find_working_stream():
#             print("Cannot start stream - no working URL found")
#             return False
        
#         print(f"\n🚀 Starting accessibility-enabled stream from: {self.current_stream_url}")
#         print("\nAccessibility Controls:")
#         print("  'n' - Normal mode")
#         print("  'd' - Deaf mode (speech-to-text)")
#         print("  'm' - Mute mode (sign language detection)")
#         print("  'b' - Blind mode (object detection + audio)")
#         print("  'q' - Quit")
        
#         # Initialize video capture
#         os.environ["OPENCV_FFMPEG_TRANSPORT_OPTION"] = "rtsp_transport=tcp"
#         self.cap = cv2.VideoCapture(self.current_stream_url, cv2.CAP_FFMPEG)
        
#         if not self.cap.isOpened():
#             print("✗ Failed to open video stream")
#             return False
        
#         # Initialize speech thread for deaf mode
#         speech_thread = None
        
#         try:
#             while True:
#                 ret, frame = self.cap.read()
#                 if not ret:
#                     print("✗ Failed to get frame")
#                     break
                
#                 # Process frame based on accessibility mode
#                 if self.accessibility_mode == "blind":
#                     frame = self.detect_objects(frame)
#                 elif self.accessibility_mode == "mute":
#                     frame = self.detect_sign_language(frame)
                
#                 # Display speech text for deaf users
#                 if self.accessibility_mode == "deaf":
#                     try:
#                         while not self.text_queue.empty():
#                             text = self.text_queue.get_nowait()
#                             cv2.putText(frame, text, (10, frame.shape[0] - 60),
#                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
#                             # Keep text visible by re-adding it
#                             if not self.text_queue.empty():
#                                 self.text_queue.put(text)
#                     except queue.Empty:
#                         pass
                
#                 # Display current mode
#                 mode_colors = {
#                     "normal": (255, 255, 255),
#                     "deaf": (0, 255, 255),
#                     "mute": (255, 0, 255),
#                     "blind": (0, 255, 0)
#                 }
#                 cv2.putText(frame, f"Mode: {self.accessibility_mode.upper()}", (10, 30),
#                            cv2.FONT_HERSHEY_SIMPLEX, 1, mode_colors.get(self.accessibility_mode, (255, 255, 255)), 2)
                
#                 cv2.imshow('CP Plus Accessibility Camera', frame)
                
#                 # Handle key presses
#                 key = cv2.waitKey(1) & 0xFF
#                 if key == ord('q'):
#                     break
#                 elif key == ord('n'):
#                     self.accessibility_mode = "normal"
#                     print("📷 Normal mode activated")
#                 elif key == ord('d') and SPEECH_AVAILABLE:
#                     self.accessibility_mode = "deaf"
#                     print("👂 Deaf mode activated - Speech-to-text enabled")
#                     if speech_thread is None or not speech_thread.is_alive():
#                         speech_thread = threading.Thread(target=self.process_speech_for_deaf, daemon=True)
#                         speech_thread.start()
#                 elif key == ord('m') and MEDIAPIPE_AVAILABLE:
#                     self.accessibility_mode = "mute"
#                     print("🤟 Mute mode activated - Sign language detection enabled")
#                 elif key == ord('b') and YOLO_AVAILABLE:
#                     self.accessibility_mode = "blind"
#                     print("👁️ Blind mode activated - Object detection with audio guidance")
                
#         except KeyboardInterrupt:
#             print("\nStopping stream...")
#         finally:
#             self.cleanup()
        
#         return True

#     def cleanup(self):
#         """Clean up resources"""
#         if self.cap:
#             self.cap.release()
#         cv2.destroyAllWindows()
#         print("✓ Cleanup completed")

# def main():
#     parser = argparse.ArgumentParser(description='CP Plus Camera with Accessibility Features')
#     parser.add_argument('--ip', default=CAMERA_IP, help='Camera IP address')
#     parser.add_argument('--port', type=int, default=PORT, help='Camera port')
#     parser.add_argument('--username', default=USERNAME, help='Camera username')
#     parser.add_argument('--password', default=PASSWORD, help='Camera password')
#     parser.add_argument('--mode', choices=['normal', 'deaf', 'mute', 'blind'], 
#                        default='normal', help='Initial accessibility mode')
    
#     args = parser.parse_args()
    
#     print("=== CP Plus Camera Accessibility System ===")
#     print("This system provides accessibility features for:")
#     print("• Deaf users: Speech-to-text display")
#     print("• Mute users: Sign language recognition")
#     print("• Blind users: Object detection with audio guidance")
#     print()
    
#     # Check feature availability
#     features = []
#     if SPEECH_AVAILABLE:
#         features.append("✓ Speech Recognition")
#     if MEDIAPIPE_AVAILABLE:
#         features.append("✓ Sign Language Detection")
#     if YOLO_AVAILABLE:
#         features.append("✓ Object Detection")
    
#     if features:
#         print("Available features:")
#         for feature in features:
#             print(f"  {feature}")
#     else:
#         print("⚠️ No accessibility features available. Install optional dependencies:")
#         print("  pip install speechrecognition pyttsx3 mediapipe ultralytics")
#     print()
    
#     try:
#         camera = CPPlusAccessibilityCamera(args.ip, args.port, args.username, args.password)
#         camera.accessibility_mode = args.mode
        
#         if camera.start_accessibility_stream():
#             print("✓ Stream completed successfully")
#         else:
#             print("✗ Stream failed to start")
            
#     except Exception as e:
#         print(f"Error: {e}")
#         print("\nTroubleshooting:")
#         print(f"1. Check camera is accessible at http://{args.ip}:{args.port}")
#         print("2. Verify credentials are correct")
#         print("3. Ensure camera supports RTSP streaming")

# if __name__ == "__main__":
#     main()


import cv2
import time
import os
import subprocess
import urllib.parse
import threading
import queue
import numpy as np
import argparse
import logging
import sys
from datetime import datetime
import json


# Optional imports for accessibility features
try:
    import speech_recognition as sr
    import pyttsx3
    SPEECH_AVAILABLE = True
    print("✓ Speech Recognition libraries loaded")
except ImportError as e:
    SPEECH_AVAILABLE = False
    print(f"⚠️ Speech features not available: {e}")
    print("Install with: pip install speechrecognition pyttsx3")

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    print("✓ MediaPipe loaded")
except ImportError as e:
    MEDIAPIPE_AVAILABLE = False
    print(f"⚠️ Sign language detection not available: {e}")
    print("Install with: pip install mediapipe")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print("✓ YOLO/Ultralytics loaded")
except ImportError as e:
    YOLO_AVAILABLE = False
    print(f"⚠️ Object detection not available: {e}")
    print("Install with: pip install ultralytics")

try:
    from onvif import ONVIFCamera
    import zeep
    ONVIF_AVAILABLE = True
    print("✓ ONVIF libraries loaded")
except ImportError as e:
    ONVIF_AVAILABLE = False
    print(f"⚠️ ONVIF not available: {e}")
    print("Install with: pip install onvif-zeep")

# Firebase integration
try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
    print("✓ Firebase Admin SDK loaded")
except ImportError as e:
    FIREBASE_AVAILABLE = False
    print(f"⚠️ Firebase Admin SDK not available: {e}")
    print("Install with: pip install firebase-admin")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Camera credentials
USERNAME = "  "
PASSWORD = "  "
CAMERA_IP = "  "
PORT = 



def zeep_pythonvalue(self, xmlvalue):
    """Custom converter for zeep to handle xsd:dateTime values properly"""
    return xmlvalue

# Patch zeep to handle custom data types if available
if ONVIF_AVAILABLE:
    zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue

class CPPlusAccessibilityCamera:
    def __init__(self, ip=CAMERA_IP, port=PORT, username=USERNAME, password=PASSWORD, 
                 frame_width=640, frame_height=480, processing_scale=0.5):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.streaming_urls = []
        self.current_stream_url = None
        self.cap = None
        
        # Frame size settings
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.processing_scale = processing_scale  # Scale for AI processing (0.5 = half size)
        
        # Performance optimization settings
        self.detection_skip_frames = 3  # Process every Nth frame for detection
        self.current_frame_count = 0
        self.last_detections = []  # Cache last detections
        self.fast_detection_mode = True  # Use faster detection settings
        
        # Accessibility features
        self.accessibility_mode = "normal"
        self.text_queue = queue.Queue()
        self.tts_queue = queue.Queue()
        self.last_guidance_time = 0
        self.running = True  # Set to True so TTS worker can start
        self.tts_thread = None
        
        # Firebase integration
        self.firebase_ready = False
        self.firebase_db = None
        self.last_finger_count = 0
        self.last_finger_time = 0
        self.finger_debounce_time = 3.0  # 1 second debounce
        self.last_voice_command_time = 0
        self.voice_debounce_time = 2.0  # 2 second debounce
        
        # Initialize accessibility components
        self.init_accessibility_components()
        self.init_firebase()
        
    def init_firebase(self):
        """Initialize Firebase using service account"""
        if not FIREBASE_AVAILABLE:
            logger.warning("❌ Firebase Admin SDK not available")
            logger.info("Install with: pip install firebase-admin")
            self.firebase_ready = False
            return
        
        try:
            logger.info("Initializing Firebase with service account...")
            
            # Look for service account file
            service_account_files = [
                "self-balancing-7a9fe-firebase-adminsdk-fbsvc-d637a35b06.json",
                "serviceAccountKey.json", 
                "service-account.json"
            ]
            
            service_file = None
            for file in service_account_files:
                if os.path.exists(file):
                    service_file = file
                    break
            
            if not service_file:
                logger.error("❌ Service account file not found!")
                logger.info("💡 Download from Firebase Console → Project Settings → Service Accounts")
                logger.info("   → Generate new private key → Save as 'firebase-service-account.json'")
                self.firebase_ready = False
                return
            
            logger.info(f"🔑 Using service account: {service_file}")
            
            # Initialize Firebase Admin
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_file)
                self.firebase_app = firebase_admin.initialize_app(cred, {
                    'databaseURL': ' '
                })
            else:
                self.firebase_app = firebase_admin.get_app()
            
            # Get database reference
            self.firebase_db = db.reference()
            
            # Test connection
            test_ref = self.firebase_db.child('test')
            test_value = f"test_{int(time.time())}"
            test_ref.set(test_value)
            result = test_ref.get()
            
            if result == test_value:
                # Initialize database structure
                base_ref = self.firebase_db.child('4_Blind_Deaf_Dumb_Assistive')
                base_ref.set({
                    'Deaf': '0',
                    'Dumb': '0',
                })
                
                self.firebase_ready = True
                logger.info("✅ Firebase service account connection successful!")
            else:
                raise Exception("Connection test failed")
                
        except Exception as e:
            logger.error(f"❌ Firebase initialization failed: {e}")
            self.firebase_ready = False
    
    def send_to_firebase(self, node, value):
        """Send data to Firebase using service account - Direct format"""
        if not self.firebase_ready or not hasattr(self, 'firebase_db'):
            logger.warning(f"🔥 Firebase not ready, skipping: {node} = {value}")
            return False
        
        try:
            ref = self.firebase_db.child(f'4_Blind_Deaf_Dumb_Assistive/{node}')
            
            # Send direct value (not object) - just the string value
            ref.set(str(value))
            
            logger.info(f"🔥 Firebase SUCCESS: {node} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Firebase send error for {node}: {e}")
            return False

    
    def send_finger_command(self, finger_count):
        """Send finger count to Firebase with debouncing"""
        current_time = time.time()
        
        # Debouncing: only send if finger count changed and enough time passed
        if (finger_count != self.last_finger_count or 
            current_time - self.last_finger_time > self.finger_debounce_time):
            
            if finger_count > 0:
                success = self.send_to_firebase("Dumb", finger_count)
                if success:
                    self.last_finger_count = finger_count
                    self.last_finger_time = current_time
                    logger.info(f"🤟 Mute Mode: Sent finger count {finger_count} to Firebase")
    
    def send_voice_command(self, command_text):
        """Process voice commands and send to Firebase"""
        current_time = time.time()
        
        # Debouncing for voice commands
        if current_time - self.last_voice_command_time < self.voice_debounce_time:
            return
        
        command_lower = command_text.lower().strip()
        
        # Check for specific commands
        if "where are you" in command_lower:
            success = self.send_to_firebase("Deaf", "1")
            if success:
                self.last_voice_command_time = current_time
                logger.info(f"👂 Deaf Mode: 'Where are you' detected - Sent 1 to Firebase")
                
        elif "im here" in command_lower or "i'm here" in command_lower or "i am here" in command_lower:
            success = self.send_to_firebase("Deaf", "2")
            if success:
                self.last_voice_command_time = current_time
                logger.info(f"👂 Deaf Mode: 'I'm here' detected - Sent 2 to Firebase")

        elif "did you eat" in command_lower or "did you eat" in command_lower or "did you eat" in command_lower:
            success = self.send_to_firebase("Deaf", "3")
            if success:
                self.last_voice_command_time = current_time
                logger.info(f"👂 Deaf Mode: 'did you eat' detected - Sent 3 to Firebase")        
        
        # You can add more voice commands here
        # elif "help me" in command_lower:
        #     self.send_to_firebase("Deaf", "3")
        # elif "emergency" in command_lower:
        #     self.send_to_firebase("Deaf", "4")
        
    def init_accessibility_components(self):
        """Initialize accessibility components if available"""
        logger.info("Initializing accessibility components...")
        
        # Initialize instance variables for feature availability
        self.speech_ready = False
        self.mediapipe_ready = False
        self.yolo_ready = False
        
        # Speech recognition and TTS
        if SPEECH_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)
                
                # Test microphone
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Start TTS worker thread
                self.start_tts_worker()
                
                self.speech_ready = True
                logger.info("✓ Speech recognition and TTS initialized successfully")
            except Exception as e:
                logger.error(f"❌ Speech initialization failed: {e}")
                self.speech_ready = False
        
        # Sign language detection
        if MEDIAPIPE_AVAILABLE:
            try:
                self.mp_hands = mp.solutions.hands
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.mp_drawing = mp.solutions.drawing_utils
                self.mediapipe_ready = True
                logger.info("✓ Sign language detection initialized successfully")
            except Exception as e:
                logger.error(f"❌ MediaPipe initialization failed: {e}")
                self.mediapipe_ready = False
        
        # Object detection
        if YOLO_AVAILABLE:
            try:
                logger.info("Loading YOLO model for fast detection...")
                # Use nano model for speed, with optimized settings
                self.yolo_model = YOLO('yolov8n.pt')  # Nano = fastest
                
                # Set model to evaluation mode for speed
                self.yolo_model.model.eval()
                
                # Configure for speed over accuracy
                self.detection_conf_threshold = 0.6  # Higher threshold = fewer false positives
                self.detection_iou_threshold = 0.5
                self.max_detections = 5  # Limit detections for speed
                
                self.yolo_ready = True
                logger.info("✓ Fast object detection model loaded successfully")
            except Exception as e:
                logger.error(f"❌ YOLO model loading failed: {e}")
                self.yolo_model = None
                self.yolo_ready = False

    def ping_camera(self):
        """Test basic network connectivity to camera"""
        logger.info(f"Testing network connectivity to {self.ip}...")
        
        if os.name == 'nt':  # Windows
            result = subprocess.run(['ping', '-n', '1', self.ip], 
                                 capture_output=True, text=True, timeout=5)
        else:  # Linux/Mac
            result = subprocess.run(['ping', '-c', '1', self.ip], 
                                 capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            logger.info(f"✓ Camera {self.ip} is reachable")
            return True
        else:
            logger.error(f"❌ Camera {self.ip} is not reachable")
            return False

    def test_http_access(self):
        """Test HTTP access to camera web interface"""
        try:
            import requests
            url = f"http://{self.ip}:{self.port}"
            logger.info(f"Testing HTTP access to {url}...")
            
            response = requests.get(url, timeout=5, auth=(self.username, self.password))
            if response.status_code == 200:
                logger.info("✓ HTTP access successful")
                return True
            else:
                logger.warning(f"⚠️ HTTP access returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ HTTP access failed: {e}")
            return False

    def get_stream_uri(self, mycam, profile):
        """Get the stream URI from a camera profile"""
        try:
            media_service = mycam.create_media_service()
            
            request = media_service.create_type('GetStreamUri')
            request.ProfileToken = profile.token
            request.StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}
            
            response = media_service.GetStreamUri(request)
            logger.info(f"✓ Got stream URI: {response.Uri}")
            return response.Uri
        except Exception as e:
            logger.error(f"❌ Error getting stream URI: {e}")
            return None

    def connect_onvif(self):
        """Connect to camera via ONVIF and get stream URLs"""
        if not ONVIF_AVAILABLE:
            logger.error("❌ ONVIF libraries not available")
            return False
            
        logger.info(f"Connecting to ONVIF camera at {self.ip}:{self.port}...")
        
        try:
            mycam = ONVIFCamera(self.ip, self.port, self.username, self.password)
            
            # Get device information
            try:
                device_info = mycam.devicemgmt.GetDeviceInformation()
                logger.info(f"✓ Successfully connected to camera via ONVIF!")
                logger.info(f"Device Information:")
                logger.info(f"  Manufacturer: {device_info.Manufacturer}")
                logger.info(f"  Model: {device_info.Model}")
                logger.info(f"  Firmware Version: {device_info.FirmwareVersion}")
                logger.info(f"  Serial Number: {device_info.SerialNumber}")
            except Exception as e:
                logger.warning(f"⚠️ Could not get device info: {e}")
            
            # Get camera profiles
            media_service = mycam.create_media_service()
            profiles = media_service.GetProfiles()
            
            logger.info(f"Found {len(profiles)} stream profiles:")
            
            # Try each profile to get a stream URL
            for i, profile in enumerate(profiles):
                logger.info(f"Profile {i+1}: {profile.Name}")
                
                stream_uri = self.get_stream_uri(mycam, profile)
                if stream_uri:
                    self.streaming_urls.append(stream_uri)
                    logger.info(f"✓ Added stream URL: {stream_uri}")
            
            return len(self.streaming_urls) > 0
            
        except Exception as e:
            logger.error(f"❌ ONVIF connection failed: {e}")
            return False

    def get_fallback_urls(self):
        """Generate common RTSP URL patterns for CP Plus cameras"""
        logger.info("Generating fallback RTSP URLs...")
        
        # URL encode password to handle special characters
        encoded_password = urllib.parse.quote(self.password)
        
        common_urls = [
            f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/cam/realmonitor?channel=1&subtype=0",
            f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/h264/ch01/main/av_stream",
            f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/Streaming/Channels/101",
            f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/live/ch00_0",
            f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/live",
            f"rtsp://{self.username}:{encoded_password}@{self.ip}:{self.port}/stream",
            f"rtsp://{self.username}:{encoded_password}@{self.ip}/stream1",
            f"rtsp://{self.username}:{encoded_password}@{self.ip}/stream2",
        ]
        
        for url in common_urls:
            logger.info(f"Adding fallback URL: {url}")
        
        self.streaming_urls.extend(common_urls)

    def test_stream_connection(self, url, timeout=10):
        """Test if a stream URL is working with better error handling"""
        logger.info(f"Testing stream: {url}")
        
        try:
            # Set OpenCV to use TCP transport for RTSP
            os.environ["OPENCV_FFMPEG_TRANSPORT_OPTION"] = "rtsp_transport=tcp"
            
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            
            # Set connection timeout
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
            
            if not cap.isOpened():
                logger.error(f"❌ Failed to open stream: {url}")
                cap.release()
                return False
            
            # Try to read a frame
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.error(f"❌ Failed to read frame from: {url}")
                cap.release()
                return False
            
            # Check frame dimensions
            height, width = frame.shape[:2]
            if height == 0 or width == 0:
                logger.error(f"❌ Invalid frame dimensions: {width}x{height}")
                cap.release()
                return False
            
            cap.release()
            logger.info(f"✓ Stream connection successful! Frame size: {width}x{height}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Stream test failed: {e}")
            return False

    def find_working_stream(self):
        """Find a working stream URL with comprehensive testing"""
        logger.info("Searching for working stream URL...")
        
        # Step 1: Test basic connectivity
        if not self.ping_camera():
            logger.error("❌ Camera not reachable. Check network connection.")
            return False
        
        # Step 2: Test HTTP access
        self.test_http_access()
        
        # Step 3: Try ONVIF discovery
        if not self.streaming_urls:
            logger.info("Attempting ONVIF discovery...")
            if not self.connect_onvif():
                logger.warning("⚠️ ONVIF discovery failed, using fallback URLs...")
                self.get_fallback_urls()
        
        if not self.streaming_urls:
            logger.error("❌ No URLs to test")
            return False
        
        # Step 4: Test each URL
        logger.info(f"Testing {len(self.streaming_urls)} URLs...")
        for i, url in enumerate(self.streaming_urls):
            logger.info(f"Testing URL {i+1}/{len(self.streaming_urls)}")
            if self.test_stream_connection(url):
                self.current_stream_url = url
                logger.info(f"✓ Working stream found: {url}")
                return True
        
        logger.error("❌ No working stream URL found")
        return False

    def start_tts_worker(self):
        """Start the TTS worker thread"""
        if hasattr(self, 'tts_engine'):
            self.tts_thread = threading.Thread(target=self.tts_worker, daemon=True)
            self.tts_thread.start()
            logger.info("✓ TTS worker thread started")

    def tts_worker(self):
        """TTS worker thread to handle speech synthesis"""
        while self.running or not self.tts_queue.empty():
            try:
                # Get text from queue with timeout
                text = self.tts_queue.get(timeout=1)
                if text is None:  # Shutdown signal
                    break
                
                # Synthesize speech
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    logger.error(f"❌ TTS synthesis error: {e}")
                    # Try to reinitialize TTS engine
                    try:
                        self.tts_engine.stop()
                        self.tts_engine = pyttsx3.init()
                        self.tts_engine.setProperty('rate', 150)
                    except:
                        pass
                
                self.tts_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ TTS worker error: {e}")
                break

    def speak_text(self, text):
        """Text-to-speech for blind users with queue system"""
        if not self.speech_ready or not hasattr(self, 'tts_queue'):
            return
        
        try:
            # Add text to TTS queue
            self.tts_queue.put(text)
        except Exception as e:
            logger.error(f"❌ TTS queue error: {e}")

    def detect_objects(self, display_frame, processing_frame=None):
        """Object detection for blind users with speed optimizations"""
        if not self.yolo_ready or not hasattr(self, 'yolo_model') or self.yolo_model is None:
            return display_frame
        
        # Use processing frame if provided, otherwise use display frame
        if processing_frame is None:
            processing_frame = display_frame
        
        # Speed optimization: Only run detection every N frames
        self.current_frame_count += 1
        run_detection = (self.current_frame_count % self.detection_skip_frames == 0)
        
        try:
            # Calculate scale factors for drawing on display frame
            scale_x = display_frame.shape[1] / processing_frame.shape[1]
            scale_y = display_frame.shape[0] / processing_frame.shape[0]
            
            if run_detection:
                # Run actual detection on reduced frame
                if self.fast_detection_mode:
                    # Use even smaller frame for detection speed
                    fast_height = min(160, processing_frame.shape[0])
                    fast_width = min(160, processing_frame.shape[1])
                    fast_frame = cv2.resize(processing_frame, (fast_width, fast_height))
                else:
                    fast_frame = processing_frame
                
                # Run YOLO with speed optimizations
                results = self.yolo_model.predict(
                    fast_frame, 
                    conf=self.detection_conf_threshold,
                    iou=self.detection_iou_threshold,
                    max_det=self.max_detections,
                    verbose=False,
                    stream=False,  # Don't use streaming for single frames
                    save=False,
                    show=False
                )
                
                # Calculate additional scale for fast frame
                if self.fast_detection_mode:
                    fast_scale_x = processing_frame.shape[1] / fast_frame.shape[1]
                    fast_scale_y = processing_frame.shape[0] / fast_frame.shape[0]
                else:
                    fast_scale_x = fast_scale_y = 1.0
                
                detections = []
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for i, box in enumerate(boxes):
                            if i >= self.max_detections:  # Limit for speed
                                break
                            try:
                                x1, y1, x2, y2 = box.xyxy[0]
                                confidence = box.conf[0]
                                class_id = int(box.cls[0])
                                
                                if confidence > self.detection_conf_threshold:
                                    class_name = self.yolo_model.names[class_id]
                                    
                                    # Scale coordinates: fast_frame -> processing_frame -> display_frame
                                    x1_proc = x1 * fast_scale_x
                                    y1_proc = y1 * fast_scale_y
                                    x2_proc = x2 * fast_scale_x
                                    y2_proc = y2 * fast_scale_y
                                    
                                    x1_scaled = int(x1_proc * scale_x)
                                    y1_scaled = int(y1_proc * scale_y)
                                    x2_scaled = int(x2_proc * scale_x)
                                    y2_scaled = int(y2_proc * scale_y)
                                    
                                    detections.append({
                                        'name': class_name,
                                        'confidence': float(confidence),
                                        'position': (x1_scaled, y1_scaled, x2_scaled, y2_scaled)
                                    })
                            except Exception as e:
                                logger.error(f"❌ Error processing detection: {e}")
                                continue
                
                # Cache detections for next frames
                self.last_detections = detections
            else:
                # Use cached detections for speed
                detections = self.last_detections
            
            # Draw all detections (current or cached)
            for detection in detections:
                x1, y1, x2, y2 = detection['position']
                class_name = detection['name']
                confidence = detection['confidence']
                
                # Use different colors for cached vs fresh detections
                color = (0, 255, 0) if run_detection else (0, 255, 255)  # Green for fresh, Yellow for cached
                
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(display_frame, f"{class_name} {confidence:.2f}", 
                           (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Provide audio guidance every 2 seconds (more frequent for blind users)
            current_time = time.time()
            if detections and (current_time - self.last_guidance_time) > 2:
                guidance = self.generate_guidance(detections, display_frame.shape)
                self.speak_text(guidance)
                self.last_guidance_time = current_time
            
            # Show detection performance info
            detection_text = "DETECTING" if run_detection else "CACHED"
            cv2.putText(display_frame, detection_text, (10, display_frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if run_detection else (0, 255, 255), 2)
            
            return display_frame
            
        except Exception as e:
            logger.error(f"❌ Object detection error: {e}")
            return display_frame

    def generate_guidance(self, detections, frame_shape):
        """Generate spatial guidance for blind users"""
        try:
            height, width = frame_shape[:2]
            guidance = []
            
            for detection in detections[:3]:  # Limit to 3 objects
                name = detection['name']
                x1, y1, x2, y2 = detection['position']
                center_x = (x1 + x2) // 2
                
                if center_x < width // 3:
                    position = "on your left"
                elif center_x > 2 * width // 3:
                    position = "on your right"
                else:
                    position = "in front of you"
                
                guidance.append(f"{name} {position}")
            
            return ", ".join(guidance) if guidance else "Scene clear"
        except Exception as e:
            logger.error(f"❌ Guidance generation error: {e}")
            return "Unable to describe scene"

    def detect_sign_language(self, display_frame, processing_frame=None):
        """Finger counting detection for mute users with Firebase integration"""
        if not self.mediapipe_ready or not hasattr(self, 'hands'):
            return display_frame
        
        # Use processing frame if provided, otherwise use display frame
        if processing_frame is None:
            processing_frame = display_frame
        
        try:
            rgb_frame = cv2.cvtColor(processing_frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            # Calculate scale factors for drawing on display frame
            scale_x = display_frame.shape[1] / processing_frame.shape[1]
            scale_y = display_frame.shape[0] / processing_frame.shape[0]
            
            finger_count = 0  # Default to 0 fingers
            
            if results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    # Draw hand landmarks with manual scaling
                    h, w = display_frame.shape[:2]
                    
                    # Draw connections manually with scaling
                    connections = self.mp_hands.HAND_CONNECTIONS
                    for connection in connections:
                        start_idx, end_idx = connection
                        start_landmark = hand_landmarks.landmark[start_idx]
                        end_landmark = hand_landmarks.landmark[end_idx]
                        
                        # Scale coordinates to display frame
                        start_x = int(start_landmark.x * processing_frame.shape[1] * scale_x)
                        start_y = int(start_landmark.y * processing_frame.shape[0] * scale_y)
                        end_x = int(end_landmark.x * processing_frame.shape[1] * scale_x)
                        end_y = int(end_landmark.y * processing_frame.shape[0] * scale_y)
                        
                        # Draw connection line
                        cv2.line(display_frame, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
                    
                    # Draw landmark points
                    landmark_points = []
                    for landmark in hand_landmarks.landmark:
                        x = int(landmark.x * processing_frame.shape[1] * scale_x)
                        y = int(landmark.y * processing_frame.shape[0] * scale_y)
                        landmark_points.append((x, y))
                        cv2.circle(display_frame, (x, y), 3, (255, 0, 0), -1)
                    
                    # Count fingers for this hand
                    hand_finger_count = self.count_fingers(hand_landmarks)
                    finger_count = max(finger_count, hand_finger_count)  # Use highest count from all hands
                    
                    if hand_finger_count > 0:
                        # Get hand bounding box for positioning text
                        x_coords = [point[0] for point in landmark_points]
                        y_coords = [point[1] for point in landmark_points]
                        x_min, x_max = min(x_coords), max(x_coords)
                        y_min, y_max = min(y_coords), max(y_coords)
                        
                        # Draw finger count number prominently
                        text = str(hand_finger_count)
                        font_scale = 3.0
                        thickness = 6
                        
                        # Calculate text size for centering
                        (text_width, text_height), baseline = cv2.getTextSize(
                            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                        
                        # Position text above the hand
                        text_x = x_min + (x_max - x_min - text_width) // 2
                        text_y = y_min - 20
                        
                        # Ensure text stays within frame
                        text_x = max(0, min(text_x, display_frame.shape[1] - text_width))
                        text_y = max(text_height, text_y)
                        
                        # Draw background rectangle for better visibility
                        bg_x1 = text_x - 10
                        bg_y1 = text_y - text_height - 10
                        bg_x2 = text_x + text_width + 10
                        bg_y2 = text_y + 10
                        
                        cv2.rectangle(display_frame, (bg_x1, bg_y1), (bg_x2, bg_y2), 
                                     (0, 0, 0), -1)  # Black background
                        cv2.rectangle(display_frame, (bg_x1, bg_y1), (bg_x2, bg_y2), 
                                     (0, 255, 255), 3)  # Yellow border
                        
                        # Draw the number
                        cv2.putText(display_frame, text, (text_x, text_y),
                                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 255), thickness)
                        
                        # Show which hand (left/right) if multiple hands detected
                        if len(results.multi_hand_landmarks) > 1:
                            hand_label = f"Hand {hand_idx + 1}"
                            cv2.putText(display_frame, hand_label, 
                                       (text_x, text_y + text_height + 30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            
            # Send finger count to Firebase (with debouncing)
            if finger_count > 0:
                self.send_finger_command(finger_count)
            
            # Display finger count and Firebase status in corner
            if finger_count > 0:
                corner_text = f"Fingers: {finger_count}"
                firebase_status = "🔥" if self.firebase_ready else "❌"
                cv2.putText(display_frame, f"{corner_text} {firebase_status}", (10, 120),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            # Display instructions for mute mode
            cv2.putText(display_frame, "Show 1-5 fingers to send commands to Firebase", 
                       (10, display_frame.shape[0] - 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            return display_frame
        except Exception as e:
            logger.error(f"❌ Sign language detection error: {e}")
            return display_frame

    def count_fingers(self, hand_landmarks):
        """Count the number of extended fingers"""
        try:
            landmarks = hand_landmarks.landmark
            
            # Finger tip and pip landmark indices
            finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
            finger_pips = [3, 6, 10, 14, 18]  # PIP joints
            finger_mcps = [2, 5, 9, 13, 17]   # MCP joints
            
            fingers_up = 0
            
            # Check each finger
            for i in range(5):
                if i == 0:  # Thumb - check horizontal extension
                    # Check if thumb is extended (distance from MCP)
                    thumb_tip = landmarks[finger_tips[i]]
                    thumb_mcp = landmarks[finger_mcps[i]]
                    
                    # Check if thumb is extended horizontally
                    thumb_distance = abs(thumb_tip.x - thumb_mcp.x)
                    if thumb_distance > 0.04:  # Threshold for thumb extension
                        fingers_up += 1
                else:  # Other fingers - check vertical extension
                    # Finger is up if tip is above PIP (lower y value)
                    tip_y = landmarks[finger_tips[i]].y
                    pip_y = landmarks[finger_pips[i]].y
                    
                    if tip_y < pip_y:  # Tip is above PIP
                        fingers_up += 1
            
            return fingers_up
        
        except Exception as e:
            logger.error(f"❌ Finger counting error: {e}")
            return 0

    def detect_basic_gestures(self, hand_landmarks):
        """Enhanced gesture detection including finger counting"""
        try:
            # Get finger count
            finger_count = self.count_fingers(hand_landmarks)
            
            # Return finger count as gesture
            if finger_count > 0:
                return f"{finger_count} finger{'s' if finger_count != 1 else ''}"
            
            return None
        except Exception as e:
            logger.error(f"❌ Gesture detection error: {e}")
            return None

    def process_speech_for_deaf(self):
        """Continuous speech recognition for deaf users with Firebase integration"""
        if not self.speech_ready or not hasattr(self, 'recognizer') or not hasattr(self, 'microphone'):
            logger.error("❌ Speech recognition not available")
            return
        
        logger.info("🎤 Starting speech recognition...")
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("🎤 Microphone calibrated, listening...")
        except Exception as e:
            logger.error(f"❌ Microphone setup failed: {e}")
            return
        
        while self.running and self.accessibility_mode == "deaf":
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                
                try:
                    text = self.recognizer.recognize_google(audio)
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    display_text = f"[{timestamp}] {text}"
                    self.text_queue.put(display_text)
                    logger.info(f"🗣️ Recognized: {text}")
                    
                    # Process voice commands for Firebase
                    self.send_voice_command(text)
                    
                except sr.UnknownValueError:
                    pass  # No speech detected
                except sr.RequestError as e:
                    logger.error(f"❌ Speech recognition service error: {e}")
                    
            except sr.WaitTimeoutError:
                pass  # Timeout is expected
            except Exception as e:
                logger.error(f"❌ Audio processing error: {e}")
                break

    def start_accessibility_stream(self):
        """Main streaming loop with accessibility features and Firebase integration"""
        if not self.find_working_stream():
            logger.error("❌ Cannot start stream - no working URL found")
            return False
        
        logger.info(f"🚀 Starting accessibility-enabled stream from: {self.current_stream_url}")
        print("\nAccessibility Controls:")
        print("  'n' - Normal mode")
        print("  'd' - Deaf mode (speech-to-text + Firebase commands)")
        print("  'm' - Mute mode (finger counting + Firebase commands)")
        print("  'b' - Blind mode (object detection + audio)")
        print("  'q' - Quit")
        print("  'r' - Reconnect stream")
        print("  'h' - Show help")
        print("  '+' - Increase frame size")
        print("  '-' - Decrease frame size")
        print("  'f' - Toggle fast detection mode (blind mode)")
        print("  '1-9' - Set detection speed (1=fastest, 9=most accurate)")
        print("\nFirebase Commands:")
        print("  Mute Mode: 1-5 fingers → sends 1-5 to 'Dumb' node")
        print("  Deaf Mode: 'where are you' → sends 1 to 'Deaf' node")
        print("  Deaf Mode: 'im here' → sends 2 to 'Deaf' node")
        print("  Deaf Mode: 'did you eat' → sends 3 to 'Deaf' node")
        
        # Initialize video capture
        os.environ["OPENCV_FFMPEG_TRANSPORT_OPTION"] = "rtsp_transport=tcp"
        self.cap = cv2.VideoCapture(self.current_stream_url, cv2.CAP_FFMPEG)
        
        # Set capture properties for frame size
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        
        # Log actual frame size
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(f"Requested frame size: {self.frame_width}x{self.frame_height}")
        logger.info(f"Actual frame size: {actual_width}x{actual_height}")
        
        if not self.cap.isOpened():
            logger.error("❌ Failed to open video stream")
            return False
        
        self.running = True
        
        # Start TTS worker if not already running
        if self.speech_ready and (not hasattr(self, 'tts_thread') or not self.tts_thread.is_alive()):
            self.start_tts_worker()
        
        speech_thread = None
        frame_count = 0
        last_fps_time = time.time()
        fps = 0
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    logger.error("❌ Failed to get frame, attempting reconnection...")
                    if not self.reconnect_stream():
                        break
                    continue
                
                frame_count += 1
                
                # Resize frame if needed (for display and processing efficiency)
                original_frame = frame.copy()
                if frame.shape[1] != self.frame_width or frame.shape[0] != self.frame_height:
                    frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                
                # Calculate FPS
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    fps = frame_count / (current_time - last_fps_time)
                    frame_count = 0
                    last_fps_time = current_time
                
                # Create smaller frame for AI processing (better performance)
                if self.processing_scale < 1.0:
                    processing_width = int(self.frame_width * self.processing_scale)
                    processing_height = int(self.frame_height * self.processing_scale)
                    processing_frame = cv2.resize(frame, (processing_width, processing_height))
                else:
                    processing_frame = frame
                
                # Process frame based on accessibility mode
                try:
                    if self.accessibility_mode == "blind":
                        frame = self.detect_objects(frame, processing_frame)
                    elif self.accessibility_mode == "mute":
                        frame = self.detect_sign_language(frame, processing_frame)
                except Exception as e:
                    logger.error(f"❌ Frame processing error: {e}")
                
                # Display speech text for deaf users
                if self.accessibility_mode == "deaf":
                    y_offset = frame.shape[0] - 140
                    displayed_texts = []
                    
                    try:
                        # Get recent texts from queue
                        while not self.text_queue.empty() and len(displayed_texts) < 3:
                            text = self.text_queue.get_nowait()
                            displayed_texts.append(text)
                        
                        # Display texts
                        for i, text in enumerate(displayed_texts):
                            cv2.putText(frame, text, (10, y_offset + i * 30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    except queue.Empty:
                        pass
                    
                    # Show Firebase status for deaf mode
                    firebase_status = "🔥 Firebase: Ready" if self.firebase_ready else "❌ Firebase: Not Connected"
                    cv2.putText(frame, firebase_status, (10, 120),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if self.firebase_ready else (0, 0, 255), 2)
                
                # Display status information
                mode_colors = {
                    "normal": (255, 255, 255),
                    "deaf": (0, 255, 255),
                    "mute": (255, 0, 255),
                    "blind": (0, 255, 0)
                }
                
                # Mode indicator
                cv2.putText(frame, f"Mode: {self.accessibility_mode.upper()}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, mode_colors.get(self.accessibility_mode, (255, 255, 255)), 2)
                
                # FPS indicator
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Stream status
                cv2.putText(frame, f"Stream: {self.ip}", (frame.shape[1] - 200, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Frame size and processing information
                cv2.putText(frame, f"Size: {frame.shape[1]}x{frame.shape[0]}", (frame.shape[1] - 150, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                if self.processing_scale < 1.0:
                    proc_size = f"{int(self.frame_width * self.processing_scale)}x{int(self.frame_height * self.processing_scale)}"
                    cv2.putText(frame, f"AI: {proc_size}", (frame.shape[1] - 150, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Show detection optimization info in blind mode
                if self.accessibility_mode == "blind":
                    y_start = 90
                    cv2.putText(frame, f"Skip: {self.detection_skip_frames}", (frame.shape[1] - 150, y_start),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                    cv2.putText(frame, f"Fast: {'ON' if self.fast_detection_mode else 'OFF'}", (frame.shape[1] - 150, y_start + 15),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                    cv2.putText(frame, f"Conf: {self.detection_conf_threshold:.1f}", (frame.shape[1] - 150, y_start + 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                
                cv2.imshow('CP Plus Accessibility Camera', frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    logger.info("Reconnecting stream...")
                    self.reconnect_stream()
                elif key == ord('h'):
                    self.show_help()
                elif key == ord('n'):
                    self.accessibility_mode = "normal"
                    logger.info("📷 Normal mode activated")
                elif key == ord('d') and self.speech_ready:
                    self.accessibility_mode = "deaf"
                    logger.info("👂 Deaf mode activated - Speech-to-text + Firebase enabled")
                    if speech_thread is None or not speech_thread.is_alive():
                        speech_thread = threading.Thread(target=self.process_speech_for_deaf, daemon=True)
                        speech_thread.start()
                elif key == ord('m') and self.mediapipe_ready:
                    self.accessibility_mode = "mute"
                    logger.info("🤟 Mute mode activated - Finger counting + Firebase enabled")
                elif key == ord('b') and self.yolo_ready:
                    self.accessibility_mode = "blind"
                    logger.info("👁️ Blind mode activated - Object detection with audio guidance")
                elif key == ord('+') or key == ord('='):
                    # Increase frame size
                    new_width = min(1920, int(self.frame_width * 1.2))
                    new_height = min(1080, int(self.frame_height * 1.2))
                    if new_width != self.frame_width or new_height != self.frame_height:
                        self.frame_width = new_width
                        self.frame_height = new_height
                        logger.info(f"📏 Frame size increased to {self.frame_width}x{self.frame_height}")
                elif key == ord('-') or key == ord('_'):
                    # Decrease frame size
                    new_width = max(320, int(self.frame_width * 0.8))
                    new_height = max(240, int(self.frame_height * 0.8))
                    if new_width != self.frame_width or new_height != self.frame_height:
                        self.frame_width = new_width
                        self.frame_height = new_height
                        logger.info(f"📏 Frame size decreased to {self.frame_width}x{self.frame_height}")
                elif key == ord('f'):
                    # Toggle fast detection mode
                    self.fast_detection_mode = not self.fast_detection_mode
                    mode_text = "ENABLED" if self.fast_detection_mode else "DISABLED"
                    logger.info(f"⚡ Fast detection mode {mode_text}")
                elif key >= ord('1') and key <= ord('9'):
                    # Set detection speed (1=fastest, 9=most accurate)
                    speed_level = key - ord('0')
                    self.detection_skip_frames = speed_level  # 1=every frame, 9=every 9th frame
                    self.detection_conf_threshold = 0.3 + (speed_level * 0.05)  # 0.35 to 0.75
                    logger.info(f"🎯 Detection speed set to level {speed_level} (skip:{self.detection_skip_frames}, conf:{self.detection_conf_threshold:.2f})")
                
        except KeyboardInterrupt:
            logger.info("Stream interrupted by user")
        except Exception as e:
            logger.error(f"❌ Stream error: {e}")
        finally:
            self.cleanup()
        
        return True

    def reconnect_stream(self):
        """Reconnect to the stream"""
        try:
            if self.cap:
                self.cap.release()
            
            time.sleep(1)  # Brief delay
            
            self.cap = cv2.VideoCapture(self.current_stream_url, cv2.CAP_FFMPEG)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
            
            if self.cap.isOpened():
                logger.info("✓ Stream reconnected successfully")
                return True
            else:
                logger.error("❌ Stream reconnection failed")
                return False
        except Exception as e:
            logger.error(f"❌ Reconnection error: {e}")
            return False

    def show_help(self):
        """Display help information"""
        help_text = f"""
=== CP Plus Accessibility Camera with Firebase Integration ===

Current Settings:
- Frame Size: {self.frame_width}x{self.frame_height}
- Processing Scale: {self.processing_scale}
- AI Processing Size: {int(self.frame_width * self.processing_scale)}x{int(self.frame_height * self.processing_scale)}
- Fast Detection: {'ENABLED' if self.fast_detection_mode else 'DISABLED'}
- Detection Skip Frames: {self.detection_skip_frames}
- Detection Confidence: {self.detection_conf_threshold:.2f}
- Firebase Status: {'✓ Connected' if self.firebase_ready else '❌ Not Connected'}

Keyboard Controls:
- 'n': Normal viewing mode
- 'd': Deaf mode (speech-to-text + Firebase commands)
- 'm': Mute mode (finger counting + Firebase commands)  
- 'b': Blind mode (object detection with audio)
- '+': Increase frame size (up to 1920x1080)
- '-': Decrease frame size (down to 320x240)
- 'f': Toggle fast detection mode (160x160 detection frames)
- '1-9': Set detection speed (1=fastest/every frame, 9=slowest/every 9th frame)
- 'r': Reconnect stream if disconnected
- 'h': Show this help
- 'q': Quit application

Accessibility Features:
- Deaf Mode: Speech-to-text + Firebase voice commands
- Mute Mode: Finger counting + Firebase finger commands (NO AUDIO)
- Blind Mode: Object detection with audio guidance

Firebase Commands:
Mute Mode (Finger Counting):
- 1 finger → sends "1" to Firebase "Dumb" node
- 2 fingers → sends "2" to Firebase "Dumb" node
- 3 fingers → sends "3" to Firebase "Dumb" node
- 4 fingers → sends "4" to Firebase "Dumb" node
- 5 fingers → sends "5" to Firebase "Dumb" node

Deaf Mode (Voice Commands):
- Say "where are you" → sends "1" to Firebase "Deaf" node
- Say "im here" → sends "2" to Firebase "Deaf" node
- Voice commands have 2-second debounce

Firebase Database Structure:
4_Blind_Deaf_Dumb_Assistive/
├── Deaf: "0"  (voice commands)
└── Dumb: "0"  (finger commands)

Speed Optimization Tips:
- Press '1' for maximum speed (detects every frame)
- Press '3' for balanced speed/accuracy (detects every 3rd frame) 
- Press '5' for moderate speed (detects every 5th frame)
- Press 'f' to enable ultra-fast 160x160 detection frames
- Use smaller frame sizes (320x240) for better performance
- Lower processing scale (0.2-0.4) for faster AI processing

Requirements:
- Speech: pip install speechrecognition pyttsx3
- Finger Counting: pip install mediapipe
- Object Detection: pip install ultralytics
- Firebase: pip install pyrebase4

Example Usage:
python camera_script.py --mode mute --width 320 --height 240 --processing-scale 0.2
"""
        print(help_text)

    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        # Stop TTS worker thread
        if hasattr(self, 'tts_queue'):
            try:
                self.tts_queue.put(None)  # Shutdown signal
            except:
                pass
        
        if hasattr(self, 'tts_thread') and self.tts_thread.is_alive():
            try:
                self.tts_thread.join(timeout=2)
            except:
                pass
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        
        # Clean up TTS engine
        if hasattr(self, 'tts_engine'):
            try:
                self.tts_engine.stop()
            except:
                pass
        if hasattr(self, 'firebase_app'):
            try:
                firebase_admin.delete_app(self.firebase_app)
                logger.info("✓ Firebase connection cleaned up")
            except:
                pass
        logger.info("✓ Cleanup completed")

def run_diagnostics():
    """Run comprehensive diagnostics"""
    print("\n=== System Diagnostics ===")
    
    # Check OpenCV
    print(f"OpenCV version: {cv2.__version__}")
    
    # Check camera connectivity with smaller frame size for testing
    camera = CPPlusAccessibilityCamera(frame_width=320, frame_height=240, processing_scale=0.5)
    
    print("\n1. Testing network connectivity...")
    camera.ping_camera()
    
    print("\n2. Testing HTTP access...")
    camera.test_http_access()
    
    print("\n3. Testing ONVIF discovery...")
    camera.connect_onvif()
    
    print("\n4. Testing fallback URLs...")
    camera.get_fallback_urls()
    
    print("\n5. Testing stream connections...")
    working_url = camera.find_working_stream()
    
    print("\n6. Testing Firebase connection...")
    if camera.firebase_ready:
        print("✓ Firebase connection ready")
    else:
        print("❌ Firebase connection failed")
    
    if working_url:
        print(f"\n✓ Diagnostics complete. Working stream found: {camera.current_stream_url}")
    else:
        print("\n❌ Diagnostics failed. No working stream found.")
        print("\nTroubleshooting suggestions:")
        print("1. Verify camera IP address and port")
        print("2. Check username and password")
        print("3. Ensure camera supports RTSP")
        print("4. Check network connectivity")
        print("5. Try accessing camera web interface directly")
        print("6. Check Firebase configuration")

def main():
    parser = argparse.ArgumentParser(description='CP Plus Camera with Accessibility Features and Firebase Integration')
    parser.add_argument('--ip', default=CAMERA_IP, help='Camera IP address')
    parser.add_argument('--port', type=int, default=PORT, help='Camera port')
    parser.add_argument('--username', default=USERNAME, help='Camera username')
    parser.add_argument('--password', default=PASSWORD, help='Camera password')
    parser.add_argument('--mode', choices=['normal', 'deaf', 'mute', 'blind'], 
                       default='normal', help='Initial accessibility mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--diagnostics', action='store_true', help='Run diagnostics only')
    
    # Frame size control
    parser.add_argument('--width', type=int, default=640, help='Frame width (default: 640)')
    parser.add_argument('--height', type=int, default=480, help='Frame height (default: 480)')
    parser.add_argument('--processing-scale', type=float, default=0.5, 
                       help='Scale for AI processing (0.1-1.0, default: 0.5 for better performance)')
    
    # Speed optimization options
    parser.add_argument('--detection-skip', type=int, default=3, 
                       help='Skip frames for detection (1=every frame, 3=every 3rd frame, default: 3)')
    parser.add_argument('--fast-mode', action='store_true', 
                       help='Enable ultra-fast detection mode (160x160 frames)')
    parser.add_argument('--detection-conf', type=float, default=0.6,
                       help='Detection confidence threshold (0.1-0.9, default: 0.6)')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate processing scale
    if args.processing_scale < 0.1 or args.processing_scale > 1.0:
        print("Error: Processing scale must be between 0.1 and 1.0")
        return
    
    print("=== CP Plus Camera Accessibility System with Firebase ===")
    print("This system provides accessibility features for:")
    print("• Deaf users: Speech-to-text + Firebase voice commands")
    print("• Mute users: Finger counting (1-5) + Firebase finger commands")
    print("• Blind users: Object detection with audio guidance")
    print(f"• Frame size: {args.width}x{args.height}")
    if args.processing_scale < 1.0:
        proc_w = int(args.width * args.processing_scale)
        proc_h = int(args.height * args.processing_scale)
        print(f"• AI processing size: {proc_w}x{proc_h} (scale: {args.processing_scale})")
    print(f"• Detection: Skip {args.detection_skip} frames, Conf {args.detection_conf}, Fast mode: {args.fast_mode}")
    print("• Firebase: Real-time database integration")
    print()
    
    # Check feature availability
    features = []
    if SPEECH_AVAILABLE:
        features.append("✓ Speech Recognition")
    if MEDIAPIPE_AVAILABLE:
        features.append("✓ Finger Counting Detection")
    if YOLO_AVAILABLE:
        features.append("✓ Object Detection")
    if ONVIF_AVAILABLE:
        features.append("✓ ONVIF Support")
    if FIREBASE_AVAILABLE:
        features.append("✓ Firebase Integration")
    
    if features:
        print("Available features:")
        for feature in features:
            print(f"  {feature}")
    else:
        print("⚠️ No accessibility features available.")
    print()
    
    if args.diagnostics:
        run_diagnostics()
        return
    
    try:
        camera = CPPlusAccessibilityCamera(
            args.ip, args.port, args.username, args.password,
            frame_width=args.width, frame_height=args.height, 
            processing_scale=args.processing_scale
        )
        camera.accessibility_mode = args.mode
        
        # Apply speed optimization settings
        camera.detection_skip_frames = args.detection_skip
        camera.fast_detection_mode = args.fast_mode
        camera.detection_conf_threshold = args.detection_conf
        
        # Show actual feature readiness
        print("Feature readiness:")
        print(f"  Speech Recognition: {'✓' if camera.speech_ready else '❌'}")
        print(f"  Finger Counting: {'✓' if camera.mediapipe_ready else '❌'}")
        print(f"  Object Detection: {'✓' if camera.yolo_ready else '❌'}")
        print(f"  ONVIF Support: {'✓' if ONVIF_AVAILABLE else '❌'}")
        print(f"  Firebase Integration: {'✓' if camera.firebase_ready else '❌'}")
        print()
        
        if camera.start_accessibility_stream():
            logger.info("✓ Stream completed successfully")
        else:
            logger.error("❌ Stream failed to start")
            print("\nTrying diagnostics mode...")
            run_diagnostics()
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print(f"1. Check camera is accessible at http://{args.ip}:{args.port}")
        print("2. Verify credentials are correct")
        print("3. Ensure camera supports RTSP streaming")
        print("4. Run with --diagnostics flag for detailed testing")
        print("5. Check Firebase configuration and internet connection")

if __name__ == "__main__":
    main()
