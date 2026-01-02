"""
CV Integration Service - Enhanced with pricing validation and better error handling
Works with existing codebase methods
"""

import os
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv

from src.cv_analysis.condition_evaluator import ConditionEvaluator
from src.external.product_specs_extractor import ProductSpecsExtractor
from src.pricing.price_calculator import PriceCalculator
from src.nlp_engine.bilingual_report_generator import BilingualReportGenerator, validate_pricing_logic

class CVIntegrationService:
    """
    Main service orchestrating CV → Pricing → Report workflow.
    Supports both database-driven and web-search-driven pricing.
    """
    
    def __init__(self):
        """
        Simple initialization using existing codebase structure.
        Works with PriceCalculator that handles both database and web search.
        """
        load_dotenv()
        
        # Initialize core services
        self.condition_evaluator = ConditionEvaluator()
        self.specs_extractor = ProductSpecsExtractor()
        self.report_generator = BilingualReportGenerator()
        
        # Initialize pricing calculator
        # Check if SERPAPI is available
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        
        if self.serpapi_key:
            print("✅ SERPAPI configured - will use for pricing fallback")
            self.price_calculator = PriceCalculator(
                use_web_search=True,
                serpapi_key=self.serpapi_key
            )
        else:
            print("⚠️ SERPAPI not found - using database only")
            self.price_calculator = PriceCalculator(use_web_search=False)
    
    def process_complete_workflow(
        self, 
        product_name: str, 
        product_type: str,
        usage_years: float,
        gemini_analysis: dict
    ) -> dict:
        """
        Complete workflow: Specs → Price → Condition → Report
        
        Args:
            product_name: e.g. "iPhone 15 Pro"
            product_type: "mobile" or "laptop"
            usage_years: How long device has been used
            gemini_analysis: CV results from page2 (st.session_state.analysis_results)
        
        Returns:
            {
                "success": bool,
                "pricing": {...},
                "report": {"english": str, "arabic": str},
                "validation": {...},  # NEW: pricing validation results
                "error": str (if failed)
            }
        """
        
        try:
            # Step 1: Parse product name
            brand, model = self._parse_product_name(product_name)
            
            # Step 2: Evaluate condition from CV analysis
            print(f"🔍 Evaluating condition from CV analysis...")
            cv_output = self.condition_evaluator.evaluate_from_gemini(
                gemini_analysis, usage_years
            )
            
            # IMPORTANT: Add usage_years to cv_output for report generator
            cv_output['usage_years'] = usage_years
            
            # Step 3: Get product specifications
            print(f"📦 Extracting specs for: {product_name}")
            
            try:
                product_specs = self.specs_extractor.extract_specs(
                    brand, model, product_type
                )
            except Exception as e:
                print(f"⚠️ Specs extraction failed: {e}")
                # Create minimal specs if extraction fails
                product_specs = {
                    'product_name': product_name,
                    'brand': brand,
                    'model': model,
                    'specifications': {}
                }
            
            # Step 4: Calculate pricing
            # PriceCalculator.calculate_used_price handles both database and web search
            print(f"💰 Calculating pricing...")
            
            pricing_data = self.price_calculator.calculate_used_price(
                brand, model, cv_output, category=product_type
            )
            
            if not pricing_data:
                return {
                    "success": False,
                    "error": "price_not_found",
                    "message": f"Could not find pricing data for '{product_name}'"
                }
            
            # Step 4.5: NEW - Validate pricing logic
            print(f"✅ Validating pricing logic...")
            
            market_price = None
            if pricing_data.get('search_details'):
                market_price = pricing_data['search_details'].get('best_price')
            
            validation = validate_pricing_logic(
                used_price=pricing_data.get('calculated_used_price', 0),
                new_price=pricing_data.get('reference_new_price', 0),
                market_price=market_price,
                condition=cv_output.get('overall_condition', 'good')
            )
            
            # Print warnings if any
            if not validation['valid']:
                print("⚠️ PRICING VALIDATION WARNINGS:")
                for warning in validation['warnings']:
                    print(f"   {warning}")
            else:
                print(f"✅ Pricing validated: {validation['discount']:.0f}% discount looks reasonable")
            
            # Step 5: Generate bilingual report
            print(f"📝 Generating bilingual report with Gemini...")
            
            search_details = pricing_data.get('search_details')
            
            try:
                bilingual_report = self.report_generator.generate_complete_report(
                    product_specs=product_specs,
                    cv_data=cv_output,
                    pricing_data=pricing_data,
                    search_details=search_details
                )
                
                # Check if report generation succeeded
                report_status = bilingual_report.get('status', 'unknown')
                if report_status == 'fallback':
                    print("⚠️ Using fallback report (API issue)")
                elif report_status == 'success':
                    print("✅ Report generated successfully")
                    
            except Exception as e:
                print(f"❌ Report generation failed: {e}")
                # Generate minimal report
                bilingual_report = self._generate_minimal_report(
                    product_name, cv_output, pricing_data
                )
            
            # Step 6: Build success response
            response = self._build_success_response(
                product_name=product_name,
                brand=brand,
                model=model,
                product_type=product_type,
                usage_years=usage_years,
                cv_output=cv_output,
                product_specs=product_specs,
                pricing_data=pricing_data,
                bilingual_report=bilingual_report,
                validation=validation,  # NEW: include validation
                from_database=bool(pricing_data.get('price_metadata', {}).get('source') == 'database')
            )
            
            return response
            
        except Exception as e:
            print(f"❌ Workflow Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": f"Processing failed: {str(e)}"
            }
    
    def _parse_product_name(self, product_name: str) -> Tuple[str, str]:
        """Extract brand and model from product name"""
        parts = product_name.split(maxsplit=1)
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            return product_name, product_name
    
    def _generate_minimal_report(
        self, 
        product_name: str, 
        cv_output: Dict, 
        pricing_data: Dict
    ) -> Dict:
        """
        Generate a minimal report when Gemini API fails completely.
        """
        condition = cv_output.get('overall_condition', 'good')
        used_price = pricing_data.get('calculated_used_price', 0)
        new_price = pricing_data.get('reference_new_price', 0)
        discount = pricing_data.get('discount_percentage', 0)
        
        english = (
            f"This {product_name} is in {condition} condition and has been "
            f"professionally inspected. The fair market price is EGP {used_price:,.2f}, "
            f"representing a {discount:.0f}% discount from the original price of "
            f"EGP {new_price:,.2f}."
        )
        
        arabic = (
            f"جهاز {product_name} في حالة {condition} وتم فحصه بشكل احترافي. "
            f"السعر العادل في السوق هو {used_price:,.2f} جنيه مصري، "
            f"مما يمثل خصم {discount:.0f}٪ من السعر الأصلي البالغ {new_price:,.2f} جنيه مصري."
        )
        
        return {
            'english': english,
            'arabic': arabic,
            'full_text': f"{english}\n\n{arabic}",
            'status': 'minimal_fallback'
        }
    
    def _build_success_response(
        self,
        product_name: str,
        brand: str,
        model: str,
        product_type: str,
        usage_years: float,
        cv_output: Dict,
        product_specs: Dict,
        pricing_data: Dict,
        bilingual_report: Dict,
        validation: Dict,  # NEW parameter
        from_database: bool = True
    ) -> Dict:
        """Build standardized success response with validation info"""
        
        response = {
            'success': True,
            'data_source': 'database' if from_database else 'web_search',
            'product_info': {
                'name': product_name,
                'brand': brand,
                'model': model,
                'type': product_type,
                'usage_years': usage_years
            },
            'cv_analysis': cv_output,
            'product_specs': product_specs,
            'pricing': pricing_data,
            'pricing_validation': validation,  # NEW: validation results
            'report': {
                'english': bilingual_report.get('english', ''),
                'arabic': bilingual_report.get('arabic', ''),
                'full_text': bilingual_report.get('full_text', ''),
                'status': bilingual_report.get('status', 'unknown')
            }
        }
        
        # Add warnings section if validation found issues
        if not validation['valid']:
            response['warnings'] = validation['warnings']
        
        return response
    
    def get_pricing_only(
        self, 
        product_name: str, 
        product_type: str, 
        usage_years: float
    ) -> dict:
        """
        Quick pricing without CV analysis (for testing).
        Uses default 'good' condition.
        """
        try:
            brand, model = self._parse_product_name(product_name)
            
            # Use default condition
            default_condition = {
                'overall_condition': 'good',
                'condition_score': 7,
                'detected_issues': []
            }
            
            # Use PriceCalculator which handles both database and web search
            pricing = self.price_calculator.calculate_used_price(
                brand, model, default_condition, category=product_type
            )
            
            if pricing:
                # Validate pricing
                market_price = None
                if pricing.get('search_details'):
                    market_price = pricing['search_details'].get('best_price')
                
                validation = validate_pricing_logic(
                    used_price=pricing.get('calculated_used_price', 0),
                    new_price=pricing.get('reference_new_price', 0),
                    market_price=market_price,
                    condition='good'
                )
                
                return {
                    "success": True, 
                    "pricing": pricing,
                    "validation": validation
                }
            else:
                return {"success": False, "error": "Pricing calculation failed"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_existing_pricing(
        self,
        used_price: float,
        new_price: float,
        market_price: Optional[float],
        condition: str
    ) -> Dict:
        """
        Public method to validate pricing from external source.
        Useful for debugging or manual price checks.
        """
        return validate_pricing_logic(
            used_price=used_price,
            new_price=new_price,
            market_price=market_price,
            condition=condition
        )


# ============================================
# HELPER FUNCTIONS FOR STREAMLIT INTEGRATION
# ============================================

def display_pricing_validation(validation: Dict) -> None:
    """
    Display validation results in Streamlit UI.
    Usage in page3_report.py:
    
    if 'validation' in result['pricing_validation']:
        display_pricing_validation(result['pricing_validation'])
    """
    try:
        import streamlit as st
        
        if validation['valid']:
            st.success(f"✅ Pricing validated: {validation['discount']:.0f}% discount is reasonable")
        else:
            st.warning("⚠️ Pricing Validation Warnings:")
            for warning in validation['warnings']:
                st.warning(warning)
    except ImportError:
        # Not in Streamlit environment, just print
        if validation['valid']:
            print(f"✅ Pricing validated: {validation['discount']:.0f}% discount is reasonable")
        else:
            print("⚠️ Pricing Validation Warnings:")
            for warning in validation['warnings']:
                print(f"  {warning}")


def format_pricing_summary(pricing_data: Dict, validation: Dict = None) -> str:
    """
    Format pricing data for display.
    Returns a formatted string with all pricing details.
    """
    lines = []
    
    # Basic pricing
    lines.append(f"**Original Price:** EGP {pricing_data.get('reference_new_price', 0):,.2f}")
    lines.append(f"**Used Price:** EGP {pricing_data.get('calculated_used_price', 0):,.2f}")
    lines.append(f"**Discount:** {pricing_data.get('discount_percentage', 0):.0f}%")
    
    # Market comparison if available
    if pricing_data.get('search_details', {}).get('best_price'):
        market = pricing_data['search_details']['best_price']
        lines.append(f"**Market Average:** EGP {market:,.2f}")
    
    # Validation status
    if validation:
        if validation['valid']:
            lines.append("✅ **Status:** Pricing validated")
        else:
            lines.append("⚠️ **Status:** Review recommended")
            for warning in validation['warnings']:
                lines.append(f"  - {warning}")
    
    return "\n".join(lines)