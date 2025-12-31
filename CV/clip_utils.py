"""
CLIP model utilities for image classification and view validation
"""
import streamlit as st
import torch
from PIL import Image
try:
    from transformers import CLIPProcessor, CLIPModel
except ImportError:
    from transformers.models.clip import CLIPProcessor, CLIPModel

from config import (
    CLIP_PRODUCT_LABELS,
    CLIP_PRODUCT_CLASS_TO_NAME,
    CATEGORY_TO_CLIP_CLASS,
    VIEW_CLIP_LABELS,
    CLIP_TOP1_TOP2_MARGIN,
    CLIP_EXPECTED_VS_UNRELATED,
    CLIP_MAX_UNRELATED_ALLOWED,
    VIEW_REQUIRED_MARGINS,
    CONFIG
)

# ---------------- Load CLIP ----------------
@st.cache_resource
def load_clip():
    """Load and cache CLIP model"""
    model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
    processor = CLIPProcessor.from_pretrained(
        "openai/clip-vit-large-patch14",
        use_fast=True
    )
    model.eval()
    return model, processor

# Global CLIP model instance
_clip_model, _clip_processor = load_clip()

# ---------------- CLIP Core ----------------
def clip_logits(image, labels):
    """Compute CLIP logits for image-text pairs"""
    inputs = _clip_processor(text=labels, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = _clip_model(**inputs)
    logits = outputs.logits_per_image.squeeze(0)
    probs = torch.softmax(logits, dim=0)
    return logits, probs

# ---------------- CLIP Same-Device Consistency ----------------
def clip_product_check(uploaded_files, selected_category):
    """
    Verify all images belong to the selected product category
    
    Args:
        uploaded_files: Dict of {view_name: file} uploaded images
        selected_category: Expected product category ("Laptop" or "Mobile")
    
    Returns:
        Tuple of (is_valid, predicted_category, per_view_details)
    """
    expected_idx = CATEGORY_TO_CLIP_CLASS[selected_category]
    rejected, votes, per_view = [], [], {}

    for view, file in uploaded_files.items():
        img = Image.open(file).convert("RGB")
        logits, probs = clip_logits(img, CLIP_PRODUCT_LABELS)

        top2 = torch.topk(logits, 2)
        margin = float(top2.values[0] - top2.values[1])
        top_idx = int(top2.indices[0])

        reasons = []
        if CLIP_PRODUCT_CLASS_TO_NAME[top_idx] == "Unrelated":
            reasons.append("predicted Unrelated")
        if margin < CLIP_TOP1_TOP2_MARGIN:
            reasons.append("low confidence margin")
        if probs[2] > CLIP_MAX_UNRELATED_ALLOWED:
            reasons.append("high unrelated probability")
        if (logits[expected_idx] - logits[2]) < CLIP_EXPECTED_VS_UNRELATED:
            reasons.append("selected category not dominant")

        per_view[view] = {
            "top": CLIP_PRODUCT_CLASS_TO_NAME[top_idx],
            "prob": float(probs[top_idx]),
            "margin": margin,
            "reasons": reasons
        }

        if reasons:
            rejected.append(view)
        else:
            votes.append(top_idx)

    if rejected:
        return False, "Unrelated / wrong product images", per_view

    majority = max(set(votes), key=votes.count)
    return majority == expected_idx, CLIP_PRODUCT_CLASS_TO_NAME[majority], per_view

def clip_view_check(image_file, view_name):
    """
    Validate that an image matches the expected view
    
    Args:
        image_file: Uploaded image file
        view_name: Expected view name
    
    Returns:
        Tuple of (is_valid, reasons_list, info_dict)
    """
    image_file.seek(0)
    labels = VIEW_CLIP_LABELS.get(view_name)
    if labels is None:
        return True, [], {}

    img = Image.open(image_file).convert("RGB")
    logits, probs = clip_logits(img, labels)

    top2 = torch.topk(logits, 2)
    margin = float(top2.values[0] - top2.values[1])
    top_idx = int(top2.indices[0])
    
    # Determine product type from view name
    product_type = "Laptop"
    for mobile_view in ["Front screen", "Back panel", "Left side (buttons)", 
                        "Right side (buttons)", "Bottom edge (charging port)", "Camera close-up"]:
        if view_name == mobile_view:
            product_type = "Mobile"
            break
            
    REQUIRED_MARGIN = VIEW_REQUIRED_MARGINS.get(
        view_name,
        CONFIG[product_type]["required_margin"]
    )

    reasons = []
    if top_idx != 0:
        reasons.append(f"Matching failed: {labels[top_idx]}")
    if margin < REQUIRED_MARGIN:
        reasons.append(f"Image not clear enough (Confidence margin: {margin:.2f})")
    
    info = {
        "predicted": labels[top_idx],
        "prob": float(probs[top_idx]),
        "margin": margin
    }

    return len(reasons) == 0, reasons, info
