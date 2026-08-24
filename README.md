# 👓 Smart Eyewear for Inclusive Communication

An AI-powered assistive camera system designed to support **Deaf, Mute, and Blind** users through real-time computer vision, speech processing, and gesture recognition — built as a step toward accessible, inclusive smart eyewear.

## 📌 Overview

This project connects to a live camera feed (via ONVIF/RTSP) and processes the video stream in real time to provide accessibility support tailored to different needs:

- **👂 Deaf Mode** — Converts spoken speech into on-screen text and detects specific voice commands.
- **🤟 Mute Mode** — Detects hand gestures/finger counts using MediaPipe and relays them as communication signals.
- **👁️ Blind Mode** — Detects and identifies nearby objects using YOLO object detection, then gives spoken (audio) guidance on their position (left / right / in front).
- **📷 Normal Mode** — Standard camera view with no processing overlay.

Detected signals (gesture/finger counts, voice commands) are pushed to **Firebase Realtime Database**, enabling the system to communicate state to a companion device or app in real time.

## ✨ Key Features

- 🎥 Real-time video stream processing via OpenCV, with ONVIF camera auto-discovery and RTSP fallback URL detection
- 🗣️ Speech-to-text using `speech_recognition`, with text-to-speech (TTS) feedback via `pyttsx3`
- ✋ Hand gesture / finger-count detection using **MediaPipe Hands**
- 📦 Real-time object detection using **YOLOv8 (Ultralytics)** with spatial audio guidance for blind users
- ☁️ **Firebase Realtime Database** integration to sync detected gestures and voice commands to external devices
- ⚡ Performance optimizations: frame skipping, detection caching, and confidence thresholds tuned for real-time use on modest hardware
- 🔌 Graceful degradation — each accessibility module (speech, gesture, object detection) loads independently, so the system still runs if optional dependencies are missing

## 🛠️ Tech Stack

| Category | Tools / Libraries |
|---|---|
| Computer Vision | OpenCV, MediaPipe, Ultralytics YOLOv8 |
| Speech | SpeechRecognition, pyttsx3 |
| Camera Streaming | ONVIF (`onvif-zeep`), RTSP |
| Cloud / Sync | Firebase Admin SDK (Realtime Database) |
| Language | Python |

## 📂 Project Structure

```
Smart-Eyewear-for-Inclusive-Communication/
├── guesture.py      # Main accessibility camera system (ONVIF streaming, detection modes, Firebase sync)
├── handswipe.py      # Hand swipe / gesture detection module
└── README.md
```

## ⚙️ Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sahana-nd/Smart-Eyewear-for-Inclusive-Communication.git
   cd Smart-Eyewear-for-Inclusive-Communication
   ```

2. **Install dependencies**
   ```bash
   pip install opencv-python numpy speechrecognition pyttsx3 mediapipe ultralytics onvif-zeep firebase-admin requests
   ```

3. **Configure camera credentials**
   Update the `USERNAME`, `PASSWORD`, `CAMERA_IP`, and `PORT` fields in `guesture.py` with your ONVIF-compatible camera's details.

4. **Configure Firebase**
   Add your Firebase service account JSON file (e.g., `serviceAccountKey.json`) to the project root and update the `databaseURL` field in the script.

5. **Run the system**
   ```bash
   python guesture.py --mode normal
   ```

## 🎮 Usage / Controls

Once the stream starts, use these keys to switch modes:

| Key | Mode |
|---|---|
| `n` | Normal mode |
| `d` | Deaf mode (speech-to-text) |
| `m` | Mute mode (gesture detection) |
| `b` | Blind mode (object detection + audio guidance) |
| `q` | Quit |

## 🚀 Future Improvements

- Migrate detection pipeline onto embedded hardware (e.g., ESP32) for true wearable eyewear form factor
- Expand sign language detection beyond finger counts to full gesture/word vocabulary
- Add a companion mobile app to consume Firebase updates in real time
- Improve detection speed further for low-power edge deployment

## 📄 Related Publication

This project is based on research published as **"Smart Eyewear for Inclusive Communication"** in the *IRJCS Journal* (Volume 12, Issue 09, November 2025).

## 👩‍💻 Author

**Sahana N**
📧 sahana.nn09@gmail.com
🔗 [LinkedIn](https://www.linkedin.com/in/sahana-n-418841286)
