from PIL import Image
import imagehash
import io
import numpy as np
import cv2

try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
except Exception:
    # If imports fail, set imported symbols to None so caller can detect
    CLIPModel = None
    CLIPProcessor = None
    torch = None

_model = None
_processor = None


def _load():
    global _model, _processor
    if _model is None:
        if CLIPModel is None or CLIPProcessor is None:
            raise RuntimeError("transformers or torch not available. Install requirements.txt")
        _model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


def _to_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def compute_embedding(image_bytes):
    _load()
    img = _to_image(image_bytes)
    inputs = _processor(images=img, return_tensors="pt")
    with torch.no_grad():
        img_feat = _model.get_image_features(**inputs)
        img_feat = img_feat / img_feat.norm(p=2, dim=-1, keepdim=True)
    return img_feat.cpu().numpy().reshape(-1)


def text_embedding(text):
    _load()
    inputs = _processor(text=[text], return_tensors="pt")
    with torch.no_grad():
        txt_feat = _model.get_text_features(**inputs)
        txt_feat = txt_feat / txt_feat.norm(p=2, dim=-1, keepdim=True)
    return txt_feat.cpu().numpy().reshape(-1)


def _cos_sim(a, b):
    a = np.array(a)
    b = np.array(b)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def is_duplicate_embedding(a, b, thresh=0.95):
    return _cos_sim(a, b) >= thresh


def view_similarity_score(image_bytes, view_text):
    try:
        img_e = compute_embedding(image_bytes)
        txt_e = text_embedding(view_text)
        return _cos_sim(img_e, txt_e)
    except Exception:
        return 0.0


def analyze_damage(image_bytes):
    """Zero-shot damage detection using CLIP similarity. Returns list of issues.

    Each issue: {label, score, severity}
    """
    labels = ["scratches", "crack", "dent", "stain"]
    try:
        img_e = compute_embedding(image_bytes)
    except Exception:
        return []

    results = []
    for lab in labels:
        txt = f"a photo showing {lab}"
        txt_e = text_embedding(txt)
        score = _cos_sim(img_e, txt_e)
        if score > 0.25:
            if score > 0.40:
                sev = "high"
            elif score > 0.32:
                sev = "medium"
            else:
                sev = "low"
            results.append({"label": lab, "score": score, "severity": sev})
    return results


def is_blurry(image_bytes, thresh=100.0):
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return True, 0.0
    lap = cv2.Laplacian(img, cv2.CV_64F)
    var = float(lap.var())
    return (var < thresh), var


def image_phash(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return imagehash.phash(img)


def is_duplicate_phash(h1, h2, max_bits_diff=6):
    # h1,h2 are imagehash objects or integers
    return (h1 - h2) <= max_bits_diff


# If core libraries are missing, export None for callable utilities so callers
# (like `app.py`) can detect unavailability and show friendly messages
if CLIPModel is None or CLIPProcessor is None or torch is None:
    compute_embedding = None
    text_embedding = None
    is_duplicate_embedding = None
    view_similarity_score = None
    analyze_damage = None
    is_blurry = None
    image_phash = None
    is_duplicate_phash = None

# (Module exports utility functions only. Example usage should be done
# from the application code, not at import-time.)



# import streamlit as st
# from PIL import Image
# import io
# import base64

# try:
#     from cv_utils import (
#         compute_embedding,
#         is_duplicate_embedding,
#         view_similarity_score,
#         analyze_damage
#     )
# except Exception:
#     compute_embedding = None
#     is_duplicate_embedding = None
#     view_similarity_score = None
#     analyze_damage = None

# # ---------------- Configuration ----------------
# PROTOTYPE_VIEWS = {
#     "Prototype (2 views)": {
#         "num_views": 2,
#         "views": [
#             "Front view",
#             "Screen close-up"
#         ]
#     },
#     "Laptop": {
#         "num_views": 8,
#         "views": [
#             "Screen (open, front view)",
#             "Keyboard & trackpad",
#             "Top lid (closed)",
#             "Left side ports",
#             "Right side ports",
#             "Bottom panel",
#             "Corners & edges (close-up)",
#             "Charger & accessories"
#         ]
#     },
#     "Mobile": {
#         "num_views": 7,
#         "views": [
#             "Front screen",
#             "Back panel",
#             "Left side",
#             "Right side",
#             "Top edge",
#             "Bottom edge (charging port)",
#             "Camera close-up"
#         ]
#     }
# }


# def get_inspection_views(product_type):
#     return PROTOTYPE_VIEWS[product_type]


# # ---------------- Session State Init ----------------
# if "step" not in st.session_state:
#     st.session_state.step = 1

# if "inspection" not in st.session_state:
#     st.session_state.inspection = None

# if "product_type" not in st.session_state:
#     st.session_state.product_type = None

# if "uploaded_files" not in st.session_state:
#     st.session_state.uploaded_files = {}

# if "embeddings" not in st.session_state:
#     st.session_state.embeddings = {}


# # ---------------- Page 1: Product Selection ----------------
# if st.session_state.step == 1:
#     st.set_page_config(page_title="Dynamic Pricing – Inspection Setup")

#     st.title("Dynamic Pricing – Inspection Setup")

#     product_type = st.selectbox(
#         "Select product category",
#         options=["Prototype (2 views)", "Laptop", "Mobile"]
#     )

#     base_price = st.number_input("Base market price (USD)", min_value=1, value=500)
#     usage_years = st.number_input("Usage duration (years)", min_value=0, value=1)

#     if st.button("Next"):
#         st.session_state.product_type = product_type
#         st.session_state.inspection = get_inspection_views(product_type)
#         st.session_state.uploaded_files = {}
#         st.session_state.embeddings = {}
#         st.session_state.base_price = float(base_price)
#         st.session_state.usage_years = float(usage_years)
#         st.session_state.step = 2
#         st.rerun()


# # ---------------- Page 2: Photo Upload & Analysis ----------------
# elif st.session_state.step == 2:
#     st.title("Upload Product Photos — Prototype")

#     inspection = st.session_state.inspection

#     st.info(
#         f"Please upload {inspection['num_views']} photos "
#         f"for your {st.session_state.product_type}"
#     )

#     for view in inspection["views"]:
#         uploaded = st.file_uploader(
#             label=view,
#             type=["jpg", "jpeg", "png"],
#             key=view
#         )
#         st.session_state.uploaded_files[view] = uploaded

#     col1, col2 = st.columns(2)

#     with col1:
#         if st.button("Back"):
#             st.session_state.step = 1
#             st.rerun()

#     with col2:
#         if st.button("Analyze & Recommend"):
#             if None in list(st.session_state.uploaded_files.values()):
#                 st.error("Please upload all required views before analysis.")
#             else:
#                 if compute_embedding is None:
#                     st.error("CV utilities not available. Install requirements and restart.")
#                 else:
#                     results = {}
#                     embeddings = {}
#                     # Duplicate detection & view consistency
#                     for view, file in st.session_state.uploaded_files.items():
#                         content = file.read()
#                         emb = compute_embedding(content)
#                         embeddings[view] = emb

#                     # check duplicates
#                     dup_warnings = []
#                     views = list(embeddings.keys())
#                     for i in range(len(views)):
#                         for j in range(i + 1, len(views)):
#                             if is_duplicate_embedding(embeddings[views[i]], embeddings[views[j]]):
#                                 dup_warnings.append(f"{views[i]} and {views[j]} look like duplicates")

#                     if dup_warnings:
#                         st.warning("; ".join(dup_warnings))

#                     # view consistency
#                     view_mismatch = []
#                     for view, file in st.session_state.uploaded_files.items():
#                         file.seek(0)
#                         content = file.read()
#                         score = view_similarity_score(content, view)
#                         results[view] = {"view_score": score}
#                         if score < 0.22:
#                             view_mismatch.append(f"{view} may not match expected view (score {score:.2f})")

#                     if view_mismatch:
#                         st.info("View mismatch checks:\n" + "; ".join(view_mismatch))

#                     # damage analysis
#                     damage_report = {}
#                     total_deduction = 0.0
#                     deduction_map = {
#                         "scratches": 0.10,
#                         "crack": 0.25,
#                         "dent": 0.08,
#                         "stain": 0.03
#                     }

#                     for view, file in st.session_state.uploaded_files.items():
#                         file.seek(0)
#                         content = file.read()
#                         issues = analyze_damage(content)
#                         damage_report[view] = issues
#                         for iss in issues:
#                             typ = iss.get("label")
#                             sev = iss.get("severity", "low")
#                             base_pct = deduction_map.get(typ, 0.05)
#                             if sev == "low":
#                                 mult = 0.6
#                             elif sev == "medium":
#                                 mult = 1.0
#                             else:
#                                 mult = 1.6
#                             total_deduction += base_pct * mult

#                     # usage depreciation
#                     usage_years = st.session_state.get("usage_years", 1)
#                     usage_depr = min(0.6, 0.05 * usage_years)

#                     final_multiplier = max(0.05, 1.0 - usage_depr - total_deduction)
#                     base_price = st.session_state.get("base_price", 500)
#                     final_price = round(base_price * final_multiplier, 2)

#                     # simple explanation (placeholder for LLM)
#                     issues_summary = []
#                     for v, iss in damage_report.items():
#                         if iss:
#                             issues_summary.append(f"{v}: {', '.join([f'{i['label']}({i['severity']})' for i in iss])}")

#                     explanation = (
#                         f"Recommended price: ${final_price}. "
#                         f"Base ${base_price} with usage depreciation {usage_depr*100:.0f}% and damage deductions {total_deduction*100:.0f}%. "
#                         f"Detected issues: {'; '.join(issues_summary) if issues_summary else 'none detected.'}"
#                     )

#                     st.success(f"Recommended price: ${final_price}")
#                     st.markdown("**Explanation:**")
#                     st.write(explanation)

#                     st.markdown("**Damage report by view**")
#                     for v, iss in damage_report.items():
#                         st.write(v)
#                         if not iss:
#                             st.write("No issues detected")
#                         else:
#                             for item in iss:
#                                 st.write(f"- {item['label']} (severity: {item['severity']}, score: {item['score']:.2f})")

#                     st.markdown("**Uploaded images**")
#                     for v, file in st.session_state.uploaded_files.items():
#                         file.seek(0)
#                         img = Image.open(io.BytesIO(file.read()))
#                         st.image(img, caption=v, use_column_width=True)

