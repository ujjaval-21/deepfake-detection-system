import os
from PIL import Image
import cv2

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def extract_image_metadata(image_path):
    metadata = {}

    try:
        image = Image.open(image_path)
        info = image._getexif()

        if info:
            metadata['has_exif'] = True
            metadata['camera_make'] = info.get(271, 'Unknown')
            metadata['camera_model'] = info.get(272, 'Unknown')
        else:
            metadata['has_exif'] = False

    except:
        metadata['has_exif'] = False

    return metadata


def extract_video_metadata(video_path):
    metadata = {}

    cap = cv2.VideoCapture(video_path)

    metadata['frame_width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    metadata['frame_height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    metadata['fps'] = cap.get(cv2.CAP_PROP_FPS)
    metadata['frame_count'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cap.release()

    return metadata
