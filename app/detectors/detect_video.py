import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model

IMG_SIZE = 224
MAX_SEQ_LENGTH = 20
NUM_FEATURES = 2048

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "video_model", "deepfake_video_model.keras")

def build_feature_extractor():
    feature_extractor = tf.keras.applications.InceptionV3(
        weights="imagenet",
        include_top=False,
        pooling="avg",
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
    )
    preprocess_input = tf.keras.applications.inception_v3.preprocess_input

    inputs = tf.keras.Input((IMG_SIZE, IMG_SIZE, 3))
    preprocessed = preprocess_input(inputs)
    outputs = feature_extractor(preprocessed)
    return tf.keras.Model(inputs, outputs, name="feature_extractor")

# Initialize feature extractor globally to avoid reloading
feature_extractor = build_feature_extractor()

if os.path.exists(MODEL_PATH):
    model = load_model(MODEL_PATH, compile=False)
    print(f"✅ Video model loaded successfully from: {MODEL_PATH}")
else:
    print(f"⚠️ Warning: Video model NOT found at {MODEL_PATH}")
    print("Please run 'train_video_model.py' first to generate the model file.")
    model = None


def prepare_single_video(frames):
    """
    Extracts features from video frames and creates a sequence for the RNN.
    """
    frame_features = np.zeros(shape=(1, MAX_SEQ_LENGTH, NUM_FEATURES), dtype="float32")
    frame_mask = np.zeros(shape=(1, MAX_SEQ_LENGTH,), dtype="bool")

    video_length = len(frames)
    length = min(MAX_SEQ_LENGTH, video_length)

    for i in range(length):
        # Resize and preprocess the frame
        frame = cv2.resize(frames[i], (IMG_SIZE, IMG_SIZE))
        frame = frame[:, :, [2, 1, 0]]  # BGR to RGB
        frame = np.expand_dims(frame, axis=0)
        
        # Extract features (2048-dim vector)
        frame_features[0, i, :] = feature_extractor.predict(frame, verbose=0)
        frame_mask[0, i] = 1  # Mark frame as active

    return frame_features, frame_mask

def analyze_video(video_path):
    """
    The main interface function for your Flask/App logic.
    Returns: (Label, Confidence, Error)
    """
    if model is None:
        return "Unknown", "Model not loaded", "Model file missing"

    if not os.path.exists(video_path):
        return "Error", "File not found", f"Could not find video at {video_path}"

    cap = cv2.VideoCapture(video_path)
    frames = []
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
            # Only take up to MAX_SEQ_LENGTH frames for detection
            if len(frames) == MAX_SEQ_LENGTH:
                break
    finally:
        cap.release()

    if len(frames) == 0:
        return "Error", "0%", "Video file is empty or corrupted"

    # Prepare features for the RNN model
    X_features, X_mask = prepare_single_video(frames)
    
    prediction = model.predict([X_features, X_mask])[0]
    
    score = float(prediction[0])
    is_fake = score > 0.5
    
    label = "Fake" if is_fake else "Real"
    confidence = score if is_fake else (1 - score)
    
    return label, f"{confidence * 100:.2f}%", None