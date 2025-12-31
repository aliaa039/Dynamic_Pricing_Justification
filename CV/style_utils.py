import streamlit as st
import requests

def inject_custom_css():
    st.markdown("""
        <style>
        /* 1. Hide default Streamlit sidebar navigation links */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* 2. Global Font & Background settings */
        .stApp {
            background-color: #f8f9fa !important;
            color: #1f2937 !important;
            font-family: 'Inter', sans-serif;
        }

        /* 3. Font Size Adjustments */
        h1 { font-size: 2.2rem !important; font-weight: 800 !important; color: #111827 !important; }
        h2 { font-size: 1.8rem !important; font-weight: 700 !important; color: #1f2937 !important; }
        h3 { font-size: 1.4rem !important; font-weight: 600 !important; color: #374151 !important; }
        p, span, label { font-size: 1rem !important; }

        /* 4. Resello Branding Header */
        .brand-header {
            display: flex;
            align-items: center;
            padding: 1rem 0;
            margin-bottom: 2rem;
            border-bottom: 1px solid #e5e7eb;
        }
        .brand-title {
            font-size: 1.8rem !important;
            font-weight: 900 !important;
            color: #007bff !important;
            margin-left: 10px;
        }

        /* 5. Report Cards Styling */
        .report-card {
            background: white !important;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            border-left: 4px solid #007bff;
            margin-bottom: 15px;
            color: #1f2937 !important;
        }

        /* 6. RTL Support for Arabic */
        .rtl-text {
            direction: rtl !important;
            text-align: right !important;
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
        }

        /* 7. Metric Styling */
        [data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            font-weight: 700 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

AI_SCAN_ANIM = "https://lottie.host/8e3d0385-e64e-4e4a-b582-7f37452d37c8/Kq4E5pW1nL.json"