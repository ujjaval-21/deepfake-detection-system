import os
import uuid
import urllib.request
from detectors.detect_video import analyze_video

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def analyze_link(video_url, upload_folder):
    """
    Downloads video from given URL and performs deepfake detection.
    """

    # Generate a local filename
    file_name = f"{uuid.uuid4()}.mp4"

    local_path = os.path.join(upload_folder, file_name)

    # Download the video
    urllib.request.urlretrieve(video_url, local_path)

    # Reuse video detection logic
    confidence_score = analyze_video(local_path)

    return confidence_score
