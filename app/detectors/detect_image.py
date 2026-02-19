import os
import cv2
from detectors.metadata_analyzer import extract_image_metadata

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def analyze_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    texture_score = gray.var()

    metadata = extract_image_metadata(image_path)

    metadata_warning = False
    if not metadata['has_exif']:
        metadata_warning = True

    # Combine metadata + texture logic
    if texture_score < 200 or metadata_warning:
        detection_result = "Likely Deepfake"
        confidence_score = "82%"
    elif texture_score < 600:
        detection_result = "Uncertain"
        confidence_score = "55%"
    else:
        detection_result = "Likely Real"
        confidence_score = "88%"

    return detection_result, confidence_score, metadata
