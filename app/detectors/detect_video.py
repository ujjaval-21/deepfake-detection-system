import os
import cv2
import numpy as np
import tensorflow as tf
import subprocess
from tensorflow.keras.models import load_model
from detectors.metadata_analyzer import extract_video_metadata


IMG_SIZE = 224
MAX_SEQ_LENGTH = 20
NUM_FEATURES = 2048

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR, "..", "models", "video_model", "deepfake_video_model.keras"
)

#Convert Codic
def convert_to_mp4(input_path):
    output_path = input_path.rsplit(".", 1)[0] + "_converted.mp4"

    command = [
        "ffmpeg",
        "-i", input_path,
        "-vcodec", "libx264",
        "-acodec", "aac",
        "-y",
        output_path
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_path


# FEATURE EXTRACTOR
def build_feature_extractor():
    base_model = tf.keras.applications.InceptionV3(
        weights="imagenet",
        include_top=False,
        pooling="avg",
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
    )

    preprocess_input = tf.keras.applications.inception_v3.preprocess_input

    inputs = tf.keras.Input((IMG_SIZE, IMG_SIZE, 3))
    x = preprocess_input(inputs)
    outputs = base_model(x)

    return tf.keras.Model(inputs, outputs, name="feature_extractor")

feature_extractor = build_feature_extractor()

# LOAD MODEL
if os.path.exists(MODEL_PATH):
    model = load_model(MODEL_PATH, compile=False)
    print(f"✅ Video model loaded from: {MODEL_PATH}")
else:
    print(f"❌ Model NOT found at: {MODEL_PATH}")
    model = None


# FEATURE PREPARATION
def prepare_single_video(frames):
    frame_features = np.zeros((1, MAX_SEQ_LENGTH, NUM_FEATURES), dtype="float32")
    frame_mask = np.zeros((1, MAX_SEQ_LENGTH), dtype="bool")

    length = min(len(frames), MAX_SEQ_LENGTH)

    for i in range(length):
        try:
            frame = cv2.resize(frames[i], (IMG_SIZE, IMG_SIZE))
            frame = frame[:, :, [2, 1, 0]]  # BGR → RGB
            frame = np.expand_dims(frame, axis=0)

            features = feature_extractor.predict(frame, verbose=0)

            frame_features[0, i, :] = features
            frame_mask[0, i] = 1

        except Exception as e:
            print(f"⚠️ Frame processing error at index {i}: {e}")

    return frame_features, frame_mask


# MAIN FUNCTION (USED IN FLASK)
def analyze_video(video_path):
    """
    Returns:
    label (Real/Fake)
    confidence (%)
    error (None or message)
    """

    # ❌ Model not loaded
    if model is None:
        return "Error", "0%", None, None

    if not os.path.exists(video_path):
        return "Error", "0%", None, None
    
    converted_path = convert_to_mp4(video_path)
    if not os.path.exists(converted_path):
        return "Error", "0%", None, None

    cap = cv2.VideoCapture(converted_path)
    frames = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frames.append(frame)

            # Limit frames for speed
            if len(frames) >= MAX_SEQ_LENGTH:
                break

    except Exception as e:
        cap.release()
        return "Error", "0%", None, None

    finally:
        cap.release()

    # ❌ No frames extracted
    if len(frames) == 0:
        return "Error", "0%", None, None

    # FEATURE EXTRACTION
    X_features, X_mask = prepare_single_video(frames)

    try:
        prediction = model.predict([X_features, X_mask], verbose=0)[0]

        score = float(prediction[0])

        label = "Fake" if score > 0.5 else "Real"
        confidence = score if score > 0.5 else (1 - score)

        metadata = extract_video_metadata(converted_path)

        return label, f"{confidence * 100:.2f}%", metadata, converted_path
    
    except Exception as e:
       return "Error", "0%", None, None