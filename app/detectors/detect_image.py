from transformers import ViTImageProcessor, ViTForImageClassification
from .metadata_analyzer import extract_image_metadata
from PIL import Image
import torch

# Load model once
model_path = "models/image_model"

processor = ViTImageProcessor.from_pretrained(model_path)
model = ViTForImageClassification.from_pretrained(model_path)

model.eval()

labels = ["real", "fake"]

def analyze_image(image_path):
    image = Image.open(image_path).convert("RGB")

    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    probs = torch.softmax(logits, dim=1)

    confidence = probs.max().item() * 100
    pred = torch.argmax(probs, dim=1).item()

    label = labels[pred]

    metadata = extract_image_metadata(image_path)

    return label, f"{confidence:.2f}%", metadata
    