import requests
import json
import os
import re
from typing import Dict, Optional
from dotenv import load_dotenv

class BilingualReportGenerator:
    def __init__(self):
        load_dotenv()
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.model_id = "gemini-2.5-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:generateContent?key={self.google_key}"

    def generate_complete_report(self, product_specs, cv_data, pricing_data, search_details=None) -> Dict:
        """
        بياخد المواصفات ويحولها لفقرات تحليلية (English & Arabic).
        """
        # تحضير المواصفات كمتغير نصي للـ Prompt
        specs = product_specs.get('specifications', {})
        specs_summary = "\n".join([f"- {k}: {v}" for k, v in specs.items()])
        
        usage = cv_data.get('usage_years', '1.0')
        price = pricing_data.get('calculated_used_price', 0)

        prompt = f"""You are a professional technology reviewer. Write a detailed valuation report.
        
        --- TECHNICAL SPECS ---
        {specs_summary}
        
        --- CONTEXT ---
        Product: {product_specs.get('product_name')}
        Usage: {usage} years | Condition: {cv_data.get('overall_condition')}
        Market Price: EGP {price:,.2f}

        TASK:
        1. Write 3 long, professional paragraphs in English under [REPORT_EN].
        2. Describe how the specs justify the fair price.
        3. Write 3 matching paragraphs in Arabic under [REPORT_AR] using professional terms.
        """

        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                full_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            
                en_report, ar_report = self._split_bilingual_report(full_text)
                
                return {
                    "english": en_report,
                    "arabic": ar_report,
                    "full_text": full_text
                }
            else:
                return self._generate_fallback_report(product_specs, cv_data, pricing_data)
                
        except Exception as e:
            print(f"❌ Generator Error: {str(e)}")
            return self._generate_fallback_report(product_specs, cv_data, pricing_data)

    def _split_bilingual_report(self, text):
        en_match = re.search(r'\[REPORT_EN\](.*?)(?=\[REPORT_AR\]|$)', text, re.DOTALL)
        ar_match = re.search(r'\[REPORT_AR\](.*?)$', text, re.DOTALL)
        
        en_text = en_match.group(1).strip() if en_match else text
        ar_text = ar_match.group(1).strip() if ar_match else "جاري تجهيز التقرير العربي..."
        
        return en_text, ar_text

    def _generate_fallback_report(self, product_specs, cv_data, pricing_data):
        specs = product_specs.get('specifications', {})
        specs_list = "\n".join([f"• {k}: {v}" for k, v in specs.items()])
        price = pricing_data.get('calculated_used_price', 0)
        
        return {
            "english": f"Professional Valuation Report\nPrice: EGP {price:,.2f}\nSpecs:\n{specs_list}",
            "arabic": f"تقرير التقييم الاحترافي\nالسعر المقدر: {price:,.2f} جنيه مصري\nالمواصفات:\n{specs_list}"
        }