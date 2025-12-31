# 📱 Dynamic Pricing & Justification System

**AI-Powered Re-commerce Valuation Engine** 

---

## 🌟 Project Overview

This project is an end-to-end **AI Valuation System** designed for the re-commerce market. It provides a fair market price for used electronics by combining **Computer Vision (CV)** to assess physical condition and **Natural Language Processing (NLP)** to extract real-time market data and technical specifications.

---

## 🛠 Project Structure

The project is divided into two primary modules:

### 1. Computer Vision (CV) Module

* **Purpose**: Analyzes the device's physical condition (scratches, cracks, usage) through uploaded images.
* **Tech Stack**: Streamlit, Google Gemini Vision.
* **Key Functions**: Condition scoring, issue detection, and visual assessment.

### 2. Natural Language Processing (NLP) Module

* **Purpose**: Scans the web for live pricing and technical specifications.
* **Tech Stack**: Flask, Google Gemini 2.5 Flash, SerpAPI.
* **Key Functions**: Real-time spec extraction, market price benchmarking, and bilingual report generation (English & Arabic).

---

## 🚀 Getting Started

### Prerequisites

* **Python**: 3.10 or 3.11 (Recommended)
* **Conda**: For environment management.
* **API Keys**: Required in `.env` file:
* `GOOGLE_API_KEY`: For Gemini 2.5 Flash.
* `SERPAPI_KEY`: For live Google Search results.



### Installation

1. **Clone the Repository**:
```bash
git clone https://github.com/yourusername/Dynamic_Pricing_Justification.git
cd Dynamic_Pricing_Justification

```


2. **Setup Environment**:
```bash
conda activate pricing_env
# Install dependencies
pip install -r requirements.txt

```


3. **Configure `.env**`:
Create a `.env` file in the root directory and add your keys as shown in `.env.example`.

---

## 🖥 How to Run

### I. Running the CV Module (UI)

The CV module uses **Streamlit** for a smooth, interactive user experience.

```bash
cd CV
conda activate pricing_env
streamlit run app.py

```

> **Note**: This will launch the web interface at `http://localhost:8501`.

### II. Running the NLP/Backend Engine

The NLP engine runs as a **Flask API** to handle pricing requests and report generation.

```bash
# Open a new terminal
cd NLP_Engine
python -m api.main

```

> **Endpoints**:
> * `POST /cv-to-pricing`: The main integration endpoint.
> * `POST /extract-specs`: To get technical data from the web.
> 
> 

---

## ⚠️ Maintenance & Troubleshooting

* **Python Version**: If you see a `FutureWarning` regarding Python 3.10, consider upgrading to **Python 3.11** for long-term support with Google's core libraries.
* **Library Updates**: The project is transitioning from `google-generativeai` to the new `google-genai` package. Ensure you keep your dependencies updated.
* **API Quota**: Since this uses **Gemini 2.5 Flash**, be mindful of the Daily Request Limit (RPD) in the free tier (currently 20 requests/day).

---
