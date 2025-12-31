import streamlit as st
import os
from dotenv import load_dotenv
from style_utils import inject_custom_css

load_dotenv()

# Import Page Modules
from clip_utils import load_clip
from pages import page1_product_info, page2_upload_photos, page3_report

# ---------------- Session State Initialization ----------------
def init_session_state():
    defaults = {
        "step": 1,
        "product_name": "",
        "product_type": "Mobile",
        "usage_years": 0.0,
        "inspection": None,
        "uploaded_files": {},
        "analysis_results": {},
        "gemini_api_key": os.getenv("GOOGLE_API_KEY", "")
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()
_clip_model, _clip_processor = load_clip()

# ---------------- UI Logic ----------------
def main():
    inject_custom_css()
    
    # Custom Sidebar (Hidden Default Nav)
    with st.sidebar:
        # Fixed Branding Header
        st.markdown("""
            <div style='display: flex; align-items: center; margin-bottom: 20px;'>
                <img src='https://cdn-icons-png.flaticon.com/512/2103/2103633.png' width='40'>
                <span style='font-size: 24px; font-weight: 900; color: #007bff; margin-left: 10px;'>RESELLO</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### AI Inspector Panel")
        st.divider()
        
        st.info(f"📍 Current Step: {st.session_state.step} / 3")
        
        if st.session_state.product_name:
            st.success(f"📦 Device: **{st.session_state.product_name}**")

    # Page Navigation Logic
    if st.session_state.step == 1:
        page1_product_info.render()
    elif st.session_state.step == 2:
        page2_upload_photos.render()
    elif st.session_state.step == 3:
        page3_report.render()

if __name__ == "__main__":
    main()