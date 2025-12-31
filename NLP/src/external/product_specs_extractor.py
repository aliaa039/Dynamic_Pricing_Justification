import requests
import json
import os
import re
from typing import Dict, Optional
from dotenv import load_dotenv

class ProductSpecsExtractor:
    def __init__(self):
        load_dotenv()
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.model_id = "gemini-2.5-flash"
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:generateContent?key={self.google_key}"

    def extract_specs(self, brand: str, model: str, category: Optional[str] = None) -> Dict:
        """
        بيسيرش في جوجل ويحول النتائج لمواصفات تقنية صريحة.
        """
        print(f"\n[Specs Extractor] 🔍 Deep-searching for: {brand} {model} using {self.model_id}")
        
        try:
            # 1 SerpAPI
            query = f"{brand} {model} full technical specifications display processor camera battery"
            params = {"q": query, "api_key": self.serpapi_key, "num": 5}
            search_res = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
            results = search_res.json().get('organic_results', [])
            
            if not results:
                return self._create_failure_response(brand, model)
            
            context = " ".join([f"{r.get('title')}: {r.get('snippet')}" for r in results[:4]])

            # 2 Gemini API
            prompt = f"""Extract full tech specs for {brand} {model} from text: {context}.
            Return ONLY a valid JSON object with keys: 'Display', 'Processor', 'RAM', 'Storage', 'Battery', 'Camera'.
            Be very detailed. No markdown formatting or backticks."""

            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            ai_res = requests.post(self.gemini_url, json=payload, timeout=20)
            
            if ai_res.status_code == 200:
                raw_text = ai_res.json()['candidates'][0]['content']['parts'][0]['text']
                # Clean up any unwanted formatting
                clean_json = re.sub(r'```json|```', '', raw_text).strip()
                
                return {
                    "product_name": f"{brand} {model}",
                    "specifications": json.loads(clean_json),
                    "extraction_status": "success"
                }
            else:
                print(f"⚠️ Gemini API Error: {ai_res.status_code}")
                return self._create_failure_response(brand, model)
                
        except Exception as e:
            print(f"❌ Extractor Error: {str(e)}")
            return self._create_failure_response(brand, model)

    def _create_failure_response(self, brand, model):
        return {
            "product_name": f"{brand} {model}",
            "specifications": {"Status": "Live data search limited"},
            "extraction_status": "failed"
        }