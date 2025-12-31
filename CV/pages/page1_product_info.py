"""
Page 1: Product Information & API Setup
"""
import streamlit as st
from gemini_utils import initialize_gemini
from validation_helpers import get_inspection_views

def render():
    st.set_page_config(page_title="Re-Commerce AI Inspector")
    st.title("🔍 Re-Commerce AI Inspector")
    st.markdown("### Step 1: Product Information")

    # Initialize Gemini if key is present in session state
    if st.session_state.gemini_api_key:
        if initialize_gemini(st.session_state.gemini_api_key):
             # Optional: show a small indicator or keep it silent
             pass
    else:
        st.warning("⚠️ No Gemini API Key found in environment variables. Please set GOOGLE_API_KEY.")
    
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input("Product Name", value=st.session_state.product_name, placeholder="e.g. iPhone 13 Pro")
        product_type = st.selectbox("Category", ["Laptop", "Mobile"])
    
    with col2:
        usage_years = st.number_input("Usage Duration (Years)", min_value=0.0, value=st.session_state.usage_years)

    # Disable if no key available
    has_key = bool(st.session_state.gemini_api_key)
    
    if st.button("Generate Inspection Plan", disabled=not has_key):
        if not product_name:
            st.error("Please enter a product name.")
        elif not has_key:
            st.error("Missing Google API Key. Please set GOOGLE_API_KEY environment variable.")
        else:
            st.session_state.product_name = product_name
            st.session_state.product_type = product_type
            st.session_state.usage_years = usage_years
            st.session_state.inspection = get_inspection_views(product_type)
            st.session_state.uploaded_files = {}
            st.session_state.step = 2
            st.rerun()
