"""
Page 3: Physical Condition Report + Send to NLP
"""
import streamlit as st
import requests
import json

NLP_API_URL = "http://localhost:5000/cv-to-pricing"

def render():
    st.title("📊 Physical Condition Report")
    
    res = st.session_state.analysis_results
    usage_years = st.session_state.usage_years
    product_name = st.session_state.product_name
    
    st.markdown(f"### Visual Inspection: **{product_name}**")
    st.markdown(f"**Usage:** {usage_years} years | **Category:** {st.session_state.product_type}")
    
    detected_issues_summary = []
    total_issues = 0
    
    # Display results per view
    for view, analysis in res.items():
        st.markdown(f"#### 📷 {view}")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(st.session_state.uploaded_files[view], width="stretch")
        
        with col2:
            issues = analysis.get("issues", [])
            overall = analysis.get("overall_condition", "unknown")
            
            if not issues or (len(issues) == 1 and "pristine" in issues[0].get("description", "").lower()):
                st.success(f"✅ **Condition:** Pristine - No damage detected")
            else:
                total_issues += len(issues)
                st.warning(f"⚠️ **Overall Condition:** {overall.upper()}")
                
                for issue in issues:
                    severity_emoji = {"low": "🟡", "medium": "🟠", "high": "🔴"}.get(issue.get("severity", "low"), "⚪")
                    st.write(f"{severity_emoji} **{issue.get('type', 'Unknown').title()}** ({issue.get('severity', 'N/A')})")
                    st.write(f"   📍 Location: {issue.get('location', 'N/A')}")
                    st.write(f"   💬 {issue.get('description', 'No description')}")
                    
                    detected_issues_summary.append(
                        f"- {view}: {issue['type']} ({issue['severity']}) at {issue['location']} - {issue['description']}"
                    )
        
        st.divider()

    # Summary Statistics
    st.markdown("## 📈 Damage Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Issues Detected", total_issues)
    with col2:
        st.metric("Views Inspected", len(res))
    with col3:
        condition_score = max(0, 100 - (total_issues * 10))
        st.metric("Condition Score", f"{condition_score}%")

    st.divider()
    
    # 🆕 NEW - Send to NLP for Pricing
    st.markdown("## 💰 Generate Pricing & Report")
    
    # Map category
    category_map = {
        "Laptop": "laptop",
        "Mobile": "smartphone"
    }
    
    if st.button("🚀 Generate Pricing & Bilingual Report", type="primary"):
        with st.spinner("Connecting to NLP service..."):
            try:
                payload = {
                    "product_name": st.session_state.product_name,
                    "product_type": category_map.get(st.session_state.product_type, "smartphone"),
                    "usage_years": st.session_state.usage_years,
                    "analysis_results": st.session_state.analysis_results
                }
                
                response = requests.post(NLP_API_URL, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("✅ Pricing analysis complete!")
                    
                    # Display pricing
                    st.markdown("### 💵 Pricing Analysis")
                    pricing = result.get('pricing', {})
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "New Price",
                            f"EGP {pricing.get('reference_new_price', 0):,.2f}"
                        )
                    with col2:
                        st.metric(
                            "Used Price",
                            f"EGP {pricing.get('calculated_used_price', 0):,.2f}",
                            delta=f"-{pricing.get('discount_percentage', 0)}%"
                        )
                    with col3:
                        st.metric(
                            "You Save",
                            f"EGP {pricing.get('reference_new_price', 0) - pricing.get('calculated_used_price', 0):,.2f}"
                        )
                    
                    # Display bilingual report
                    report = result.get('report', {})
                    
                    st.markdown("### 📄 Bilingual Report")
                    
                    tab1, tab2 = st.tabs(["🇬🇧 English", "🇪🇬 Arabic"])
                    
                    with tab1:
                        st.markdown(report.get('english', 'No English report available'))
                    
                    with tab2:
                        st.markdown(report.get('arabic', 'لا يوجد تقرير عربي'))
                    
                    # Store in session state
                    st.session_state.pricing_result = result
                    
                elif response.status_code == 404:
                    st.error("❌ Could not find market price for this product")
                    st.info("The NLP service couldn't determine a market price. Try a different product name.")
                else:
                    st.error(f"❌ NLP service error: {response.status_code}")
                    st.code(response.text)
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to NLP service")
                st.info(f"Make sure the NLP server is running at {NLP_API_URL}")
            except requests.exceptions.Timeout:
                st.error("❌ Request timeout - NLP service took too long")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.divider()

    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Start New Inspection"):
            st.session_state.step = 1
            st.session_state.uploaded_files = {}
            st.session_state.analysis_results = {}
            if "pricing_result" in st.session_state:
                del st.session_state.pricing_result
            st.rerun()
    
    with col2:
        if st.button("📥 Download Report (Coming Soon)", disabled=True):
            st.info("PDF export feature coming soon!")