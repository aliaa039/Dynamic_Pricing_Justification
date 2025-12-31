"""
Gemini API utilities for damage analysis and report generation
"""
import streamlit as st
import google.generativeai as genai
import json
import base64
from io import BytesIO
import re

# ---------------- Gemini Configuration ----------------
def initialize_gemini(api_key):
    """Initialize Gemini API with user's API key"""
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {str(e)}")
        return False

def image_to_base64(image):
    """Convert PIL Image to base64 for Gemini"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# ---------------- Gemini Validation Analysis ----------------
def verify_same_device_with_gemini(images, product_type):
    """
    Verify whether multiple photos belong to the same physical device
    
    Args:
        images: List of PIL Images
        product_type: "Laptop" or "Mobile"
    
    Returns:
        Dict with keys: same_device (bool), confidence (str), reason (str)
    """
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
You are verifying whether multiple photos belong to the SAME physical {product_type}.

This is a STRICT identity verification.

Determine whether ALL images show the SAME SINGLE DEVICE,
not just the same model or type.

Check carefully for:
- Matching scratches, dents, wear patterns
- Consistent logos, stickers, or marks
- Consistent port wear or damage
- Color tone and material consistency

If there is ANY doubt, answer NO.

Return ONLY valid JSON:
{{
  "same_device": true | false,
  "confidence": "high | medium | low",
  "reason": "brief explanation"
}}
"""

    response = model.generate_content([prompt] + images)

    text = response.text.strip()
    if text.startswith("```"):
        text = text.strip("```").replace("json", "").strip()

    return json.loads(text)


# ---------------- Gemini Damage Analysis ----------------
def analyze_damage_with_gemini(image, view_name, product_type):
    """
    Use Gemini 2.5 Flash to detect scratches and damage
    
    Args:
        image: PIL Image
        view_name: Name of the view being analyzed
        product_type: "Laptop" or "Mobile"
    
    Returns:
        Dict with keys: issues (list), overall_condition (str)
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""Analyze this {product_type} image showing the '{view_name}' view for physical damage and wear.

CRITICAL INSTRUCTIONS - BE EXTREMELY CAREFUL:
- Only report damage that is CLEARLY and UNMISTAKABLY VISIBLE
- Do NOT confuse reflections, lighting, shadows, or glare with damage
- Glass/reflective surfaces often show reflections that look like cracks - IGNORE THESE
- Camera lenses, sensors, and flash are NORMAL features, not damage
- Design elements, patterns, or textures are NOT damage
- If you're not 100% certain it's real damage, DO NOT report it

Identify ONLY if you are absolutely certain:
1. **Scratches**: Deep visible surface scratches (NOT light reflections)
2. **Cracks**: Actual physical cracks with broken material (NOT reflections or light patterns)
3. **Dents**: Physical deformations or impacts
4. **Discoloration**: Permanent stains, yellowing, or color changes
5. **Wear**: Obvious usage wear like paint loss or material degradation
6. **Broken Parts**: Missing or broken components

If the condition appears good or you're unsure, respond with pristine condition.

IMPORTANT: Return ONLY valid JSON, no markdown code blocks, no extra text:
{{
  "issues": [
    {{"type": "scratches", "severity": "medium", "location": "top-left corner", "description": "visible surface scratches"}}
  ],
  "overall_condition": "good"
}}

If pristine:
{{
  "issues": [],
  "overall_condition": "pristine"
}}"""

        response = model.generate_content([prompt, image])
        
        # Parse JSON response with better error handling
        text = response.text.strip()
        
        # Remove markdown code blocks
        # Try to extract JSON from markdown blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        else:
            # Remove any leading/trailing markdown
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        
        # Try to find JSON object even if embedded in text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        
        result = json.loads(text.strip())
        
        # Validate the result structure
        if "issues" not in result or "overall_condition" not in result:
            raise ValueError("Invalid JSON structure")
            
        return result
        
    except json.JSONDecodeError as e:
        st.warning(f"⚠️ Gemini returned invalid JSON for {view_name}")
        # Try to show what was returned
        try:
            raw_text = response.text[:300] if 'response' in locals() else "No response"
            st.code(raw_text, language="text")
        except:
            pass
        return {
            "issues": [],
            "overall_condition": "unknown"
        }
    except Exception as e:
        st.error(f"❌ Gemini API Error for {view_name}: {str(e)}")
        return {
            "issues": [],
            "overall_condition": "unknown"
        }

# ---------------- Gemini Report Generation ----------------
def generate_report_with_gemini(analysis_results, product_name, product_type, usage_years):
    """
    Use Gemini (gemini-2.5-flash) to generate a human-readable condition report
    
    Args:
        analysis_results: Dict of {view_name: analysis_result}
        product_name: Name of the product
        product_type: "Laptop" or "Mobile"
        usage_years: Years of usage
    
    Returns:
        String containing the generated report
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Build an issues summary for the prompt
        issues_lines = []
        total_issues = 0
        for view, analysis in analysis_results.items():
            issues = analysis.get("issues", [])
            if not issues:
                continue
            total_issues += len(issues)
            for iss in issues:
                issues_lines.append(f"View: {view} - {iss.get('type','unknown')} ({iss.get('severity','n/a')}) at {iss.get('location','N/A')}: {iss.get('description','')}")

        issues_text = "\n".join(issues_lines) if issues_lines else "No damage detected - pristine condition."

        prompt = f"""You are an assistant that summarizes product inspection results for a re-commerce platform.

Product: {product_name}
Category: {product_type}
Usage Duration (years): {usage_years}
Total Issues Detected: {total_issues}

Detected Issues (one per line):
{issues_text}

Please provide:
1) A concise summary of the overall physical condition.
2) How the detected damage affects resale value (qualitative guidance).
3) A fair market grade: 'Like New', 'Good', 'Fair', or 'Poor'.
4) Recommended actions for the seller (repairs, disclosure, photos to add).

Return the answer as plain text (no JSON required)."""

        response = model.generate_content([prompt])
        text = getattr(response, "text", "").strip()
        # Strip code fences if present
        if text.startswith("```"):
            parts = text.split('\n')
            if parts[0].startswith('```'):
                parts = parts[1:]
            if parts and parts[-1].strip().startswith('```'):
                parts = parts[:-1]
            text = "\n".join(parts).strip()
        return text if text else "(No response from Gemini)"
    except Exception as e:
        return f"Gemini Error: {str(e)}"
