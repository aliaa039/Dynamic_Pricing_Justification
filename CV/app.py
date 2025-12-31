"""
Re-Commerce AI Inspector - Main Application Entry Point
"""
import streamlit as st
import os
from dotenv import load_dotenv  # Added to load .env files

# 1. Load environment variables from .env file (if it exists)
load_dotenv()

# Import utility needed for initialization
from clip_utils import load_clip
from pages import page1_product_info, page2_upload_photos, page3_report

# Initialize CLIP model at startup
_clip_model, _clip_processor = load_clip()

# ---------------- Session State Initialization ----------------
# Always check environment variables on every rerun to keep state in sync
if "gemini_api_key" not in st.session_state or not st.session_state.gemini_api_key:
    # Prioritize GOOGLE_API_KEY from environment
    st.session_state.gemini_api_key = os.getenv("GOOGLE_API_KEY", "")

if "step" not in st.session_state:
    st.session_state.step = 1
if "inspection" not in st.session_state:
    st.session_state.inspection = None
if "product_type" not in st.session_state:
    st.session_state.product_type = None
if "product_name" not in st.session_state:
    st.session_state.product_name = ""
if "usage_years" not in st.session_state:
    st.session_state.usage_years = 0.0
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}

# ---------------- Main Navigation ----------------
def main():
    if st.session_state.step == 1:
        page1_product_info.render()
    elif st.session_state.step == 2:
        page2_upload_photos.render()
    elif st.session_state.step == 3:
        page3_report.render()

if __name__ == "__main__":
    main()