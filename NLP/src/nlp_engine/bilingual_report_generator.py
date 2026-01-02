import requests
import json
import os
import re
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=2):
    """Decorator for exponential backoff retry"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    # Check if it's a rate limit error
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        delay = base_delay * (2 ** attempt)
                        print(f"⏳ Rate limit hit. Waiting {delay}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(delay)
                    else:
                        raise
            return None
        return wrapper
    return decorator


class BilingualReportGenerator:
    """
    Generate concise, condition-focused pricing reports in English and Arabic.
    Uses actual CV inspection results to justify pricing.
    """
    
    def __init__(self):
        load_dotenv()
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.model_id = "gemini-2.0-flash-exp"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:generateContent?key={self.google_key}"
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests

    def _rate_limit_wait(self):
        """Ensure minimum time between API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    @retry_with_backoff(max_retries=3, base_delay=2)
    def _call_gemini_api(self, payload: Dict) -> Optional[Dict]:
        """Make API call with rate limiting and retry logic"""
        self._rate_limit_wait()
        
        response = requests.post(self.api_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            raise Exception("Rate limit exceeded (429)")
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

    def generate_complete_report(
        self, 
        product_specs: Dict, 
        cv_data: Dict, 
        pricing_data: Dict, 
        search_details: Dict = None
    ) -> Dict:
        """
        Generate concise bilingual report based on actual device condition.
        
        Args:
            product_specs: Device specifications from database
            cv_data: Computer vision inspection results (from Gemini analysis)
            pricing_data: Calculated pricing with discount
            search_details: Market search results (optional)
        
        Returns:
            {"english": str, "arabic": str, "full_text": str}
        """
        # Extract key information
        product_name = product_specs.get('product_name', 'Device')
        usage_years = cv_data.get('usage_years', 1.0)
        
        # Extract condition from CV analysis
        condition_summary = self._extract_condition_from_cv(cv_data.get('analysis_results', {}))
        
        # Pricing info
        new_price = pricing_data.get('reference_new_price', 0)
        used_price = pricing_data.get('calculated_used_price', 0)
        discount = pricing_data.get('discount_percentage', 0)
        
        # Get market comparison if available
        market_price = None
        if search_details and 'best_price' in search_details:
            market_price = search_details['best_price']
        
        # Build focused prompt
        prompt = self._build_focused_prompt(
            product_name=product_name,
            usage_years=usage_years,
            condition_summary=condition_summary,
            new_price=new_price,
            used_price=used_price,
            discount=discount,
            specs=product_specs.get('specifications', {}),
            market_price=market_price
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000
            }
        }
        
        try:
            result = self._call_gemini_api(payload)
            
            if result:
                full_text = result['candidates'][0]['content']['parts'][0]['text']
                en_report, ar_report = self._split_bilingual_report(full_text)
                
                return {
                    "english": en_report.strip(),
                    "arabic": ar_report.strip(),
                    "full_text": full_text,
                    "status": "success"
                }
                
        except Exception as e:
            print(f"❌ Report Generation Error: {str(e)}")
        
        # Fallback to template-based report
        print("⚠️ Using fallback report template")
        return self._generate_fallback_report(
            product_name, condition_summary, new_price, used_price, discount, market_price
        )

    def _extract_condition_from_cv(self, analysis_results: Dict) -> Dict:
        """
        Extract structured condition summary from CV analysis results.
        
        Input format (from page2):
        {
            "Front": {"overall_condition": "good", "damage_details": {...}},
            "Back": {"overall_condition": "excellent", ...},
            "Side": {...}
        }
        
        Output:
        {
            "overall": "good",
            "issues": ["minor scratches on back", "small dent on side"],
            "severity": "minor"  # or "moderate", "severe"
        }
        """
        if not analysis_results:
            return {
                "overall": "good",
                "issues": [],
                "severity": "none"
            }
        
        # Collect all conditions
        conditions = []
        all_issues = []
        
        for view, analysis in analysis_results.items():
            condition = analysis.get('overall_condition', 'good').lower()
            conditions.append(condition)
            
            # Extract damage details
            damage_details = analysis.get('damage_details', {})
            
            for damage_type, items in damage_details.items():
                if items and len(items) > 0:
                    severity = items[0].get('severity', 'minor') if isinstance(items, list) else 'minor'
                    all_issues.append(f"{severity} {damage_type} on {view.lower()}")
        
        # Determine overall condition (worst case)
        condition_priority = {"poor": 0, "fair": 1, "good": 2, "excellent": 3}
        overall = min(conditions, key=lambda c: condition_priority.get(c, 2))
        
        # Determine severity
        if any("severe" in issue or "major" in issue for issue in all_issues):
            severity = "severe"
        elif any("moderate" in issue for issue in all_issues):
            severity = "moderate"
        elif all_issues:
            severity = "minor"
        else:
            severity = "none"
        
        return {
            "overall": overall,
            "issues": all_issues[:3],  # Top 3 issues only
            "severity": severity
        }

    def _build_focused_prompt(
        self, 
        product_name: str,
        usage_years: float,
        condition_summary: Dict,
        new_price: float,
        used_price: float,
        discount: float,
        specs: Dict,
        market_price: Optional[float] = None
    ) -> str:
        """
        Build a focused prompt for ONE paragraph report.
        """
        # Format specs (top 3-4 only)
        key_specs = ['display', 'processor', 'ram', 'storage', 'battery', 'camera']
        specs_text = ""
        for key in key_specs:
            if key in specs:
                specs_text += f"- {key.title()}: {specs[key]}\n"
        
        # Format issues
        issues_text = ""
        if condition_summary['issues']:
            issues_text = "\n".join(f"• {issue}" for issue in condition_summary['issues'])
        else:
            issues_text = "• No significant damage detected"
        
        # Market comparison context
        market_context = ""
        if market_price and market_price > 0:
            price_diff = ((market_price - used_price) / market_price) * 100
            if abs(price_diff) > 5:  # Only mention if significant difference
                market_context = f"\nMARKET COMPARISON:\n• Similar devices selling at: EGP {market_price:,.2f}\n• Price advantage: {abs(price_diff):.0f}% {'lower' if used_price < market_price else 'higher'}\n"
        
        prompt = f"""You are a professional tech product evaluator writing a pricing justification report.

PRODUCT: {product_name}
USAGE: {usage_years} year(s)
CONDITION: {condition_summary['overall'].upper()}

INSPECTION RESULTS:
{issues_text}

KEY SPECIFICATIONS:
{specs_text if specs_text else "Standard specifications for this model"}
{market_context}
PRICING:
• Original New Price: EGP {new_price:,.2f}
• Fair Used Price: EGP {used_price:,.2f}
• Discount: {discount:.0f}%

INSTRUCTIONS:
Write EXACTLY ONE professional paragraph (5-6 sentences) that:
1. Opens with device name, usage period, and verified condition
2. References 2-3 key specifications that retain value
3. Honestly describes condition impact on pricing (mention issues if present)
4. {f'Compares to market pricing (EGP {market_price:,.2f})' if market_price else 'Justifies the discount percentage'}
5. Concludes with final price and value proposition

CRITICAL REQUIREMENTS:
- Be honest about condition issues
- Justify price based on actual inspection results
- Use professional but accessible language
- Keep it concise (one paragraph only)

Format your response EXACTLY as:

[ENGLISH]
Your English paragraph here (5-6 sentences, professional tone)

[ARABIC]
الفقرة بالعربية هنا (5-6 جمل، لغة احترافية)

Note: Arabic translation must be natural and professional, not literal word-for-word translation."""
        
        return prompt

    def _split_bilingual_report(self, text: str) -> tuple[str, str]:
        """Extract English and Arabic sections from generated text"""
        # Try to find marked sections
        en_match = re.search(r'\[ENGLISH\](.*?)(?=\[ARABIC\]|$)', text, re.DOTALL | re.IGNORECASE)
        ar_match = re.search(r'\[ARABIC\](.*?)$', text, re.DOTALL | re.IGNORECASE)
        
        if en_match and ar_match:
            return en_match.group(1).strip(), ar_match.group(1).strip()
        
        # Fallback: split by paragraph breaks
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if len(paragraphs) >= 2:
            # Detect which is Arabic by checking for Arabic characters
            if any('\u0600' <= c <= '\u06FF' for c in paragraphs[0]):
                return paragraphs[1], paragraphs[0]
            else:
                return paragraphs[0], paragraphs[1]
        
        # Last resort
        return text.strip(), "التقرير العربي غير متاح حالياً. الرجاء المحاولة مرة أخرى."

    def _generate_fallback_report(
        self,
        product_name: str,
        condition_summary: Dict,
        new_price: float,
        used_price: float,
        discount: float,
        market_price: Optional[float] = None
    ) -> Dict:
        """
        Enhanced template-based fallback if API fails.
        """
        condition = condition_summary.get('overall', 'good')
        condition_ar = {
            'excellent': 'ممتازة',
            'good': 'جيدة',
            'fair': 'مقبولة',
            'poor': 'ضعيفة'
        }.get(condition, 'جيدة')
        
        issues = condition_summary.get('issues', [])
        
        # English report
        en_report = f"This {product_name} has been professionally inspected and is in {condition} condition. "
        
        if issues:
            en_report += f"Our detailed examination revealed: {', '.join(issues)}. "
        else:
            en_report += "No significant damage or defects were detected during our thorough inspection. "
        
        # Market comparison
        if market_price and market_price > 0:
            price_diff = ((market_price - used_price) / market_price) * 100
            if used_price < market_price:
                en_report += f"Compared to similar devices on the market (EGP {market_price:,.2f}), this offers exceptional value. "
            else:
                en_report += f"Pricing reflects the verified condition and market standards (similar devices: EGP {market_price:,.2f}). "
        
        en_report += (
            f"Based on the inspection results and current condition, the fair market price is EGP {used_price:,.2f}, "
            f"which represents a {discount:.0f}% discount from the original retail price of EGP {new_price:,.2f}. "
            f"This pricing ensures fair value for both buyers and sellers based on actual device condition."
        )
        
        # Arabic report (professional translation)
        ar_report = f"تم فحص جهاز {product_name} بشكل احترافي وهو في حالة {condition_ar}. "
        
        if issues:
            ar_report += f"كشف الفحص التفصيلي عن: {', '.join(issues)}. "
        else:
            ar_report += "لم يتم اكتشاف أي أضرار أو عيوب كبيرة خلال الفحص الشامل. "
        
        # Market comparison Arabic
        if market_price and market_price > 0:
            if used_price < market_price:
                ar_report += f"مقارنة بالأجهزة المماثلة في السوق ({market_price:,.2f} جنيه مصري)، يوفر هذا الجهاز قيمة استثنائية. "
            else:
                ar_report += f"السعر يعكس الحالة المؤكدة ومعايير السوق (أجهزة مماثلة: {market_price:,.2f} جنيه). "
        
        ar_report += (
            f"بناءً على نتائج الفحص والحالة الحالية، السعر العادل في السوق هو {used_price:,.2f} جنيه مصري، "
            f"مما يمثل خصم {discount:.0f}٪ من سعر البيع الأصلي البالغ {new_price:,.2f} جنيه مصري. "
            f"يضمن هذا السعر قيمة عادلة للمشترين والبائعين بناءً على حالة الجهاز الفعلية."
        )
        
        return {
            "english": en_report,
            "arabic": ar_report,
            "full_text": f"[ENGLISH]\n{en_report}\n\n[ARABIC]\n{ar_report}",
            "status": "fallback"
        }


# ============================================
# HELPER FUNCTIONS FOR INTEGRATION
# ============================================

def format_condition_for_display(analysis_results: Dict) -> str:
    """
    Format CV analysis results for display in UI.
    Can be used in page3_report.py to show condition details.
    """
    if not analysis_results:
        return "No inspection data available"
    
    lines = []
    for view, analysis in analysis_results.items():
        condition = analysis.get('overall_condition', 'unknown').upper()
        lines.append(f"**{view}:** {condition}")
        
        damage = analysis.get('damage_details', {})
        if damage:
            for damage_type, items in damage.items():
                if items and len(items) > 0:
                    count = len(items) if isinstance(items, list) else 1
                    lines.append(f"  - {count} {damage_type}")
    
    return "\n".join(lines)


def validate_pricing_logic(
    used_price: float,
    new_price: float,
    market_price: Optional[float] = None,
    condition: str = "good"
) -> Dict:
    """
    Validate pricing makes business sense.
    Returns warnings if pricing seems off.
    """
    warnings = []
    
    # Check if used price is reasonable
    discount = ((new_price - used_price) / new_price) * 100
    
    if discount < 10:
        warnings.append("⚠️ Discount too low - used devices typically have 20-60% discount")
    elif discount > 80:
        warnings.append("⚠️ Discount too high - price may be unrealistically low")
    
    # Check against market price
    if market_price and market_price > 0:
        price_diff_pct = abs(used_price - market_price) / market_price * 100
        
        if used_price > market_price * 1.3:
            warnings.append(f"⚠️ Price {price_diff_pct:.0f}% higher than market average")
        elif used_price < market_price * 0.5:
            warnings.append(f"⚠️ Price {price_diff_pct:.0f}% lower than market average - check calculation")
    
    # Condition-based validation
    expected_discount_range = {
        'excellent': (15, 35),
        'good': (30, 50),
        'fair': (50, 70),
        'poor': (70, 85)
    }
    
    if condition in expected_discount_range:
        min_d, max_d = expected_discount_range[condition]
        if discount < min_d or discount > max_d:
            warnings.append(f"⚠️ Discount ({discount:.0f}%) unusual for {condition} condition (expected {min_d}-{max_d}%)")
    
    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "discount": discount
    }