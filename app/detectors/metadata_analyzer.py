import os
from PIL import Image
import cv2
from PIL import Image, ExifTags

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def extract_image_metadata(image_path):
    metadata = {
        "has_exif": False,
        "camera_make": "Unknown",
        "camera_model": "Unknown",
        "date_taken": "Unknown",
        "software": "Unknown",
        "gps": None
    }

    try:
        image = Image.open(image_path)
        exif = image._getexif()

        if not exif:
            return metadata

        metadata["has_exif"] = True

        # Convert EXIF tag IDs to names
        exif_data = {}
        for tag, value in exif.items():
            tag_name = ExifTags.TAGS.get(tag, tag)
            exif_data[tag_name] = value

        # Basic info
        metadata["camera_make"] = exif_data.get("Make", "Unknown")
        metadata["camera_model"] = exif_data.get("Model", "Unknown")
        metadata["date_taken"] = exif_data.get("DateTime", "Unknown")
        metadata["software"] = exif_data.get("Software", "Unknown")

        # GPS Extraction
        if "GPSInfo" in exif_data:
            gps_info = exif_data["GPSInfo"]

            def convert_to_degrees(value):
                d, m, s = value
                return float(d) + float(m)/60 + float(s)/3600

            try:
                lat = convert_to_degrees(gps_info[2])
                lon = convert_to_degrees(gps_info[4])

                if gps_info[1] == 'S':
                    lat = -lat
                if gps_info[3] == 'W':
                    lon = -lon

                metadata["gps"] = {"lat": lat, "lon": lon}
            except:
                pass

    except Exception as e:
        print("Metadata error:", e)

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
