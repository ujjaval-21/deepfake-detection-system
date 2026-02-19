import os
import librosa
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def analyze_audio(audio_path):
    """
    Analyzes an audio file for deepfake-like artifacts.
    """

    # Load audio
    y, sr = librosa.load(audio_path, sr=None)

    # Extract features
    spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
    zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))

    # Simple heuristic thresholds (demo logic)
    if spectral_centroid > 3000 and zero_crossing_rate < 0.05:
        detection_result = "Likely AI-Generated Voice"
        confidence_score = "85%"
    elif spectral_centroid > 2000:
        detection_result = "Uncertain"
        confidence_score = "55%"
    else:
        detection_result = "Likely Real Voice"
        confidence_score = "90%"

    return detection_result, confidence_score
