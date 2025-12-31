"""
Image validation helper functions
"""
import streamlit as st
from PIL import Image
import imagehash
import cv2
import numpy as np
from io import BytesIO

from config import PRODUCT_INSPECTION_VIEWS, CONFIG
from clip_utils import clip_view_check

# ---------------- Helpers ----------------
def get_inspection_views(product_type):
    """Get required views for a product type"""
    return PRODUCT_INSPECTION_VIEWS[product_type]

def compute_phash(image_file):
    """Calculate perceptual hash for duplicate detection"""
    return imagehash.phash(Image.open(image_file).convert("RGB"))

def find_duplicates(uploaded_files, threshold=5):
    """
    Find duplicate images using perceptual hashing
    
    Args:
        uploaded_files: Dict of {view_name: file}
        threshold: Hash distance threshold for duplicates
    
    Returns:
        List of tuples (view1, view2) that are duplicates
    """
    hashes, duplicates = {}, []
    for view, file in uploaded_files.items():
        h = compute_phash(file)
        for pv, ph in hashes.items():
            if abs(h - ph) <= threshold:
                duplicates.append((view, pv))
        hashes[view] = h
    return duplicates

def is_blurry(image_file, product_type):
    """
    Detect blurry images using Laplacian variance
    
    Args:
        image_file: Uploaded image file
        product_type: "Laptop" or "Mobile"
    
    Returns:
        Tuple of (is_blurry, score, level)
        level can be: "severe", "borderline", or "sharp"
    """
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
    image_file.seek(0)

    score = cv2.Laplacian(img, cv2.CV_64F).var()

    if product_type == "Laptop":
        if score < 30:
            return True, score, "severe"
        elif score < 45:
            return False, score, "borderline"
        else:
            return False, score, "sharp"

    if product_type == "Mobile":
        if score < 12:
            return True, score, "severe"
        elif score < 18:
            return False, score, "borderline"
        else:
            return False, score, "sharp"

def validate_resolution(image_file, product_type):
    """
    Check minimum resolution requirements
    
    Args:
        image_file: Uploaded image file
        product_type: "Laptop" or "Mobile"
    
    Returns:
        Tuple of (is_valid, width, height)
    """
    min_w = CONFIG[product_type]["min_width"]
    min_h = CONFIG[product_type]["min_height"]
    w, h = Image.open(image_file).size
    image_file.seek(0)
    return (w >= min_w and h >= min_h), w, h

@st.cache_data(show_spinner=False)
def get_cached_validation(file_bytes, view_name, product_type):
    """
    Cached validation combining all checks
    
    Args:
        file_bytes: Image file as bytes
        view_name: Expected view name
        product_type: "Laptop" or "Mobile"
    
    Returns:
        Tuple of (is_valid, reasons_list, info_dict)
    """
    f = BytesIO(file_bytes)
    
    ok_res, w, h = validate_resolution(f, product_type)
    if not ok_res:
        return False, [f"Resolution too low: {w}x{h}"], {}
    
    is_blur, score, level = is_blurry(f, product_type)

    if is_blur:
        return False, [f"Image too blurry ({level}, score={score:.1f})"], {}

    if level == "borderline":
        st.warning(f"⚠️ Borderline sharpness (score={score:.1f}) — accepted")
    
    v_ok, v_reasons, v_info = clip_view_check(f, view_name)
    if not v_ok:
        return False, v_reasons, v_info
        
    return True, [], v_info

def get_file_bytes(file):
    """Helper to read file bytes"""
    if file is None: 
        return None
    file.seek(0)
    b = file.read()
    file.seek(0)
    return b
