import os
import cv2
from detectors.metadata_analyzer import extract_video_metadata

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def analyze_video(video_path):
    cap = cv2.VideoCapture(video_path)
    fake_frames = 0
    total = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        score = gray.var()

        if score < 200:
            fake_frames += 1

        total += 1

    cap.release()

    if total == 0:
        return 0, {}

    visual_confidence = (fake_frames / total) * 100
    metadata = extract_video_metadata(video_path)

    return visual_confidence, metadata
