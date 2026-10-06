---
language: en
license: cc-by-nc-4.0
tags:
- pytorch
- image-classification
- computer-vision
- agriculture
- plant-disease
- crop-disease
datasets:
- Saon110/bd-crop-vegetable-plant-disease-dataset
---

# 🌾 BD Crop & Vegetable Plant Disease Classification

A ResNet50-based model achieving 96.39% accuracy for classifying 94 different crop disease conditions across 10 major crop types in Bangladesh.

## Model Details

- **Architecture**: ResNet50 with custom classifier (2048→512→94)
- **Accuracy**: 96.39% test accuracy
- **Validation Accuracy**: 96.64%
- **Classes**: 94 disease conditions
- **Training Dataset**: 19.4GB BD crop disease dataset (Saon110/bd-crop-vegetable-plant-disease-dataset)
- **Training Strategy**: Gradual unfreezing with differential learning rates
- **Training Time**: 549 minutes (30 epochs)

## Usage

```python
import torch
from torchvision import models, transforms
from PIL import Image
import numpy as np

# 1. Download model weights
from huggingface_hub import hf_hub_download
model_path = hf_hub_download(repo_id="Saon110/bd-crop-vegetable-plant-disease-model", filename="crop_veg_plant_disease_model.pth")

# 2. Setup model architecture (matching training exactly)
model = models.resnet50(weights=None)
num_ftrs = model.fc.in_features
model.fc = torch.nn.Sequential(
    torch.nn.Linear(num_ftrs, 512),
    torch.nn.ReLU(),
    torch.nn.Dropout(0.2),
    torch.nn.Linear(512, 94)
)

# 3. Load model weights with robust handling
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
checkpoint = torch.load(model_path, map_location=device)

# Handle different checkpoint formats
if isinstance(checkpoint, dict):
    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    elif 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    else:
        state_dict = checkpoint
else:
    state_dict = checkpoint

# Handle DataParallel wrapper (remove 'module.' prefix if present)
if any(key.startswith('module.') for key in state_dict.keys()):
    state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}

# Load the state dictionary
model.load_state_dict(state_dict)
model.to(device)
model.eval()

# 4. Define preprocessing transforms (same as validation)
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# 5. Class mapping (94 classes)
# Load class mapping
import json
import requests

# Option 1: Download from repo
try:
    try:
        class_path = hf_hub_download(
        repo_id="Saon110/bd-crop-vegetable-plant-disease-model",
        filename="class_mapping.json"
        )

        with open(class_path, 'r') as f:
            class_names = json.load(f)
except:
    # Option 2: Hardcoded list of classes (first few and last few shown)
    class_names = {
        "0": "Banana_Black_Pitting_or_Banana_Rust",
        "1": "Banana_Crown_Rot",
        "2": "Banana_Healthy",
        "3": "Banana_fungal_disease",
        "4": "Banana_leaf_Banana_Scab_Moth",
        "5": "Banana_leaf_Black_Sigatoka",
        "6": "Banana_leaf_Healthy",
        "7": "Banana_leaf__Black_Leaf_Streak",
        "8": "Banana_leaf__Panama_Disease.",
        "9": "Cauliflower_Bacterial_spot_rot",
        "10": "Cauliflower_Black_Rot",
        "11": "Cauliflower_Downy_Mildew",
        "12": "Cauliflower_Healthy",
        "13": "Corn_Blight",
        "14": "Corn_Common_Rust",
        "15": "Corn_Gray_Leaf_Spot",
        "16": "Corn_Healthy",
        "17": "Cotton_Aphids",
        "18": "Cotton_Army worm",
        "19": "Cotton_Bacterial blight",
        "20": "Cotton_Healthy",
        "21": "Guava_fruit_Anthracnose",
        "22": "Guava_fruit_Healthy",
        "23": "Guava_fruit_Scab",
        "24": "Guava_fruit_Styler_end_root",
        "25": "Guava_leaf_Anthracnose",
        "26": "Guava_leaf_Canker",
        "27": "Guava_leaf_Dot",
        "28": "Guava_leaf_Healthy",
        "29": "Guava_leaf_Rust",
        "30": "Jute_Cescospora Leaf Spot",
        "31": "Jute_Golden Mosaic",
        "32": "Jute_Healthy Leaf",
        "33": "Mango_Anthracnose",
        "34": "Mango_Bacterial_Canker",
        "35": "Mango_Cutting_Weevil",
        "36": "Mango_Gall_Midge",
        "37": "Mango_Healthy",
        "38": "Mango_Powdery_Mildew",
        "39": "Mango_Sooty_Mould",
        "40": "Mango_die_back",
        "41": "Papaya_Anthracnose",
        "42": "Papaya_BacterialSpot",
        "43": "Papaya_Curl",
        "44": "Papaya_Healthy",
        "45": "Papaya_Mealybug",
        "46": "Papaya_Mite_disease",
        "47": "Papaya_Mosaic",
        "48": "Papaya_Ringspot",
        "49": "Potato_Black_Scurf",
        "50": "Potato_Blackleg",
        "51": "Potato_Blackspot_Bruising",
        "52": "Potato_Brown_Rot",
        "53": "Potato_Common_Scab",
        "54": "Potato_Dry_Rot",
        "55": "Potato_Healthy_Potatoes",
        "56": "Potato_Miscellaneous",
        "57": "Potato_Pink_Rot",
        "58": "Potato_Soft_Rot",
        "59": "Rice_Blast",
        "60": "Rice_Brownspot",
        "61": "Rice_Tungro",
        "62": "Rice_bacterial_leaf_blight",
        "63": "Rice_bacterial_leaf_streak",
        "64": "Rice_bacterial_panicle_blight",
        "65": "Rice_dead_heart",
        "66": "Rice_downy_mildew",
        "67": "Rice_hispa",
        "68": "Rice_normal",
        "69": "Sugarcane_Healthy",
        "70": "Sugarcane_Mosaic",
        "71": "Sugarcane_RedRot",
        "72": "Sugarcane_Rust",
        "73": "Sugarcane_Yellow",
        "74": "Tea_Anthracnose",
        "75": "Tea_algal_leaf",
        "76": "Tea_bird_eye_spot",
        "77": "Tea_brown_blight",
        "78": "Tea_gray_light",
        "79": "Tea_healthy",
        "80": "Tea_red_leaf_spot",
        "81": "Tea_white_spot",
        "82": "Tomato_Bacterial_Spot",
        "83": "Tomato_Early_Blight",
        "84": "Tomato_Late_Blight",
        "85": "Tomato_Leaf_Mold",
        "86": "Tomato_Septoria_Leaf_Spot",
        "87": "Tomato_Spider_Mites_Two-spotted_Spider_Mite",
        "88": "Tomato_Target_Spot",
        "89": "Tomato_Tomato_Yellow_Leaf_Curl_Virus",
        "90": "Tomato_healthy",
        "91": "Wheat_Healthy",
        "92": "Wheat_septoria",
        "93": "Wheat_stripe_rust"

    }


# 6. Prediction function
def predict_image(image_path, model, transform, class_names, device, top_k=3):
    """
    Predict disease for crop image

    Args:
        image_path: Path to image file
        model: Loaded model
        transform: Image preprocessing transforms
        class_names: Dictionary mapping class indices to names
        device: Computation device (CPU/GPU)
        top_k: Number of top predictions to return

    Returns:
        List of (class_name, confidence) tuples
    """
    # Load and preprocess image
    image = Image.open(image_path).convert('RGB')
    image_tensor = transform(image).unsqueeze(0).to(device)

    # Make prediction
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]

    # Get top k predictions
    top_probs, top_indices = torch.topk(probabilities, top_k)

    # Convert to class names
    predictions = []
    for i in range(top_k):
        idx = top_indices[i].item()
        class_name = class_names[str(idx)]
        confidence = top_probs[i].item()
        predictions.append((class_name, confidence))

    return predictions

# 7. Example usage
if __name__ == "__main__":
    # Test on sample image
    image_path = "sample_crop_image.jpg"  # Replace with your image
    predictions = predict_image(image_path, model, transform, class_names, device)

    # Print results
    print(f"Predictions for {image_path}:")
    for class_name, confidence in predictions:
        print(f"{class_name}: {confidence:.4f} ({confidence*100:.2f}%)")

    # Determine if healthy or diseased
    top_prediction = predictions[0][0].lower()
    if "healthy" in top_prediction:
        print("✅ Plant appears HEALTHY")
    else:
        print("⚠️ Plant may have DISEASE")
```