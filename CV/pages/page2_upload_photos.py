"""
Page 2: Upload Product Photos & Validation
"""
import streamlit as st
from PIL import Image
from validation_helpers import get_file_bytes, get_cached_validation, find_duplicates
from clip_utils import clip_product_check
from gemini_utils import verify_same_device_with_gemini, analyze_damage_with_gemini

def render():
    st.title("📸 Upload Product Photos")
    st.markdown(f"**Product:** {st.session_state.product_name} | **Category:** {st.session_state.product_type}")

    inspection = st.session_state.inspection
    all_valid = True
    
    for view in inspection["views"]:
        st.markdown(f"### {view}")
        uploaded_file = st.file_uploader(
            f"Upload {view}",
            ["jpg", "jpeg", "png"],
            key=f"upload_{view}"
        )
        st.session_state.uploaded_files[view] = uploaded_file
        
        if uploaded_file:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(uploaded_file, width="stretch")
            with col2:
                b = get_file_bytes(uploaded_file)
                with st.spinner(f"Verifying {view}..."):
                    ok, reasons, info = get_cached_validation(b, view, st.session_state.product_type)
                
                if ok:
                    st.success(f"✅ View verified! (Confidence: {info.get('margin', 0):.2f})")
                else:
                    all_valid = False
                    st.error(f"❌ Validation failed:")
                    for r in reasons:
                        st.write(f"  - {r}")
                    if info and "predicted" in info:
                        st.info(f"Detected as: {info['predicted']}")
        else:
            all_valid = False
        
        st.divider()

    if st.button("Analyze with Gemini AI 🤖", disabled=not all_valid):
        st.info("Running consistency checks...")
        
        duplicates = find_duplicates(st.session_state.uploaded_files)
        if duplicates:
            st.error("❌ Duplicate images detected:")
            for v1, v2 in duplicates:
                st.write(f"- {v1} ≈ {v2}")
            st.stop()

        product_ok, pred_cat, _ = clip_product_check(
            st.session_state.uploaded_files,
            st.session_state.product_type
        )
        
        if not product_ok:
            st.error(f"❌ Category mismatch: Expected {st.session_state.product_type}, detected {pred_cat}")
            st.stop()


        st.success("✅ All validations passed!")
        # Re-running product check here as in original code logic (redundant but preserved)
        product_ok, pred_cat, _ = clip_product_check(
            st.session_state.uploaded_files,
            st.session_state.product_type
        )

        if not product_ok:
            st.error(f"❌ Category mismatch: Expected {st.session_state.product_type}, detected {pred_cat}")
            st.stop()

        # 🔒 SAME DEVICE CHECK — GEMINI
        st.info("🔍 Verifying that all images belong to the same device...")

        images = [
            Image.open(f).convert("RGB")
            for f in st.session_state.uploaded_files.values()
            if f is not None
        ]

        same_device_result = verify_same_device_with_gemini(
            images,
            st.session_state.product_type
        )

        if not same_device_result["same_device"]:
            st.error("❌ Images do NOT belong to the same physical device.")
            st.write(f"Reason: {same_device_result['reason']}")
            st.stop()

        st.success(
            f"✅ Same device confirmed "
            f"(confidence: {same_device_result['confidence']})"
        )

        # Gemini Damage Analysis
        st.markdown("### 🔍 Analyzing damage ...")
        analysis_results = {}
        
        progress_bar = st.progress(0)
        total_views = len(st.session_state.uploaded_files)
        
        for idx, (view, file) in enumerate(st.session_state.uploaded_files.items()):
            image_file = file
            # Ensure we are at start of file before reading
            image_file.seek(0)
            
            with st.spinner(f"Analyzing {view}..."):
                img = Image.open(image_file).convert("RGB")
                analysis_results[view] = analyze_damage_with_gemini(
                    img, 
                    view, 
                    st.session_state.product_type
                )
            progress_bar.progress((idx + 1) / total_views)
        
        st.session_state.analysis_results = analysis_results
        st.success("✅ Analysis complete!")
        st.session_state.step = 3
        st.rerun()
