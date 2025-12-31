import requests
import json
from typing import Dict

class LLMReportGenerator:
    """
    Generate professional pricing reports using Claude API
    Simple and direct - no need for LangGraph
    """
    
    def __init__(self):
        self.api_url = "https://api.anthropic.com/v1/messages"
        # API key handled by claude.ai environment
        
    def generate_pricing_report(self, cv_data: Dict, pricing_data: Dict, search_details: Dict = None) -> str:
        """
        Generate natural language report from all data
        
        Input:
        - cv_data: Condition analysis from CV team
        - pricing_data: Calculated prices
        - search_details: Market search results (optional)
        
        Output:
        - Professional markdown report
        """
        
        prompt = self._build_prompt(cv_data, pricing_data, search_details)
        
        try:
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['content'][0]['text']
            else:
                return self._generate_fallback_report(cv_data, pricing_data)
                
        except Exception as e:
            print(f"LLM Error: {e}")
            return self._generate_fallback_report(cv_data, pricing_data)
    
    def _build_prompt(self, cv_data: Dict, pricing_data: Dict, search_details: Dict = None) -> str:
        """Build comprehensive prompt for Claude"""
        
        brand = pricing_data['price_metadata']['brand']
        model = pricing_data['price_metadata']['model']
        condition = cv_data.get('overall_condition', 'good')
        condition_score = cv_data.get('condition_score', 7)
        issues = cv_data.get('detected_issues', [])
        
        new_price = pricing_data['reference_new_price']
        used_price = pricing_data['calculated_used_price']
        discount = pricing_data['discount_percentage']
        source = pricing_data['price_metadata']['source']
        
        prompt = f"""Generate a professional pricing report for a used product listing.

PRODUCT INFORMATION:
- Brand: {brand}
- Model: {model}
- Condition: {condition} ({condition_score}/10)
- Detected Issues: {len(issues)} issues found
"""
        
        if issues:
            prompt += "\nISSUES DETECTED:\n"
            for issue in issues:
                prompt += f"- {issue['severity'].capitalize()} {issue['type']} on {issue['location']}\n"
        
        prompt += f"""
PRICING ANALYSIS:
- Original New Price: EGP {new_price:,.2f}
- Calculated Used Price: EGP {used_price:,.2f}
- Discount: {discount}%
- Price Source: {source}
"""
        
        if search_details:
            prompt += f"""
MARKET RESEARCH:
- Total Results Found: {search_details.get('total_results', 0)}
- Stores Checked: {', '.join(search_details.get('stores_found', []))}
- Price Range: EGP {search_details['price_range']['min']:,.0f} - {search_details['price_range']['max']:,.0f}
"""
            if search_details.get('best_deal'):
                best = search_details['best_deal']
                prompt += f"- Best Deal: {best['store']} at EGP {best['price']:,.2f}\n"
        
        prompt += """
TASK:
Write a professional, customer-friendly report (3-4 paragraphs) that:
1. Describes the product condition honestly
2. Explains the pricing logic clearly
3. Highlights the value proposition
4. Builds buyer confidence

Use a warm, trustworthy tone. Be specific about the condition issues but emphasize the fair pricing.
Write in English. Format with markdown.
"""
        
        return prompt
    
    def _generate_fallback_report(self, cv_data: Dict, pricing_data: Dict) -> str:
        """Template-based fallback if LLM fails"""
        brand = pricing_data['price_metadata']['brand']
        model = pricing_data['price_metadata']['model']
        condition = cv_data.get('overall_condition', 'good')
        issues = cv_data.get('detected_issues', [])
        
        new_price = pricing_data['reference_new_price']
        used_price = pricing_data['calculated_used_price']
        discount = pricing_data['discount_percentage']
        
        report = f"""# {brand} {model} - Pricing Report

## Product Condition
This {brand} {model} is in **{condition}** condition. """
        
        if issues:
            report += f"Our inspection identified {len(issues)} issue(s): "
            issue_list = [f"{i['severity']} {i['type']} on {i['location']}" for i in issues]
            report += ", ".join(issue_list) + "."
        else:
            report += "No significant issues were detected during inspection."
        
        report += f"""

## Pricing Analysis
- **Original Price:** EGP {new_price:,.2f}
- **Used Price:** EGP {used_price:,.2f}
- **You Save:** {discount}% (EGP {new_price - used_price:,.2f})

## Value Proposition
This pricing reflects the actual condition of the device, ensuring you get a fair deal. The {discount}% discount accounts for the used condition while maintaining transparency about the product state.

## Recommendation
This is a solid opportunity for buyers looking for {brand} products at competitive prices.
"""
        
        return report