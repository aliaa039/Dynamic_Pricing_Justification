import streamlit as st
import requests
import json
from style_utils import inject_custom_css

NLP_API_URL = "http://localhost:5000/cv-to-pricing"

def render():
    inject_custom_css()
    
    st.title("📊 Inspection & Valuation Report")
    
    res = st.session_state.analysis_results
    usage_years = st.session_state.usage_years
    product_name = st.session_state.product_name
    product_type = st.session_state.product_type
    
    # Technical Assessment Card
    st.markdown(f"""
        <div class="report-card">
            <h3 style='margin-top:0;'>🔍 {product_name}</h3>
            <p><b>Usage:</b> {usage_years} Years | <b>Category:</b> {product_type}</p>
        </div>
    """, unsafe_allow_html=True)

    # Visual Inspection Section
    st.markdown("### 📷 Visual Inspection Details")
    total_issues = 0
    
    for view, analysis in res.items():
        with st.container():
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(st.session_state.uploaded_files[view], use_container_width=True)
            with col2:
                issues = analysis.get("issues", [])
                overall = analysis.get("overall_condition", "unknown")
                st.markdown(f"**Angle:** {view}")
                
                if not issues:
                    st.success("✅ Condition: Pristine")
                else:
                    total_issues += len(issues)
                    st.warning(f"⚠️ Condition: {overall.upper()}")
                    for issue in issues:
                        st.write(f"- {issue.get('type')}: {issue.get('description')}")

    # Pricing & Reports
    st.divider()
    if st.button("🚀 Generate Market Pricing", type="primary", use_container_width=True):
        with st.spinner("Analyzing market data..."):
            try:
                payload = {
                    "product_name": product_name,
                    "product_type": product_type.lower(),
                    "usage_years": usage_years,
                    "analysis_results": res
                }
                response = requests.post(NLP_API_URL, json=payload, timeout=45)
                
                if response.status_code == 200:
                    result = response.json()
                    pricing = result.get('pricing', {})
                    report = result.get('report', {})

                    # Removed st.balloons() as requested
                    
                    st.markdown("### 💰 Price Estimation")
                    p_col1, p_col2, p_col3 = st.columns(3)
                    p_col1.metric("Market Price", f"EGP {pricing.get('reference_new_price', 0):,.0f}")
                    p_col2.metric("Fair Used Value", f"EGP {pricing.get('calculated_used_price', 0):,.0f}")
                    p_col3.metric("Depreciation", f"{pricing.get('discount_percentage', 0)}%")

                    # Bilingual Tabs
                    st.markdown("### 📄 Technical Justification")
                    tab_en, tab_ar = st.tabs(["English Report", "التقرير الفني"])
                    with tab_en:
                        st.markdown(f'<div class="report-card">{report.get("english")}</div>', unsafe_allow_html=True)
                    with tab_ar:
                        st.markdown(f'<div class="report-card rtl-text">{report.get("arabic")}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Connection Error: {str(e)}")

    # Reset Navigation
    if st.button("🔄 Start New Inspection"):
        st.session_state.step = 1
        st.rerun()