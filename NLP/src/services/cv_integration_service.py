import os
from typing import Dict, Tuple
from dotenv import load_dotenv

# Import your custom modules
from src.cv_analysis.condition_evaluator import ConditionEvaluator
from src.external.product_specs_extractor import ProductSpecsExtractor
from src.pricing.price_calculator import PriceCalculator
from src.nlp_engine.bilingual_report_generator import BilingualReportGenerator

class CVIntegrationService:
    """
    Service layer to orchestrate the complete CV to Pricing workflow.
    Ensures data consistency between CV, Specs, and Report modules.
    """
    
    def __init__(self):
        load_dotenv()
        serpapi_key = os.getenv("SERPAPI_KEY")
        
        self.condition_evaluator = ConditionEvaluator()
        self.specs_extractor = ProductSpecsExtractor()
        self.price_calculator = PriceCalculator(
            use_web_search=True,
            serpapi_key=serpapi_key
        )
        self.report_generator = BilingualReportGenerator()
    
    def process_complete_workflow(
        self,
        product_name: str,
        product_type: str,
        usage_years: float,
        gemini_analysis: Dict
    ) -> Dict:
        """
        Complete workflow logic.
        """
        # Step 1: Parse brand and model
        brand, model = self._parse_product_name(product_name)
        
        # Step 2: Evaluate physical condition
        cv_output = self.condition_evaluator.evaluate_from_gemini(
            gemini_analysis, usage_years
        )
        
        # 🆕 FIX 1: Explicitly add usage_years to cv_output 
        # Without this, the Report Generator will show "N/A"
        cv_output['usage_years'] = usage_years 
        
        # Step 3: Extract technical specifications (Dynamic Search)
        product_specs = self.specs_extractor.extract_specs(
            brand, model, product_type
        )
        
        # Step 4: Calculate fair market used price
        pricing_data = self.price_calculator.calculate_used_price(
            brand, model, cv_output, category=product_type
        )
        
        if not pricing_data:
            return self._handle_price_not_found(product_name, cv_output)
        
        # Step 5: Generate the final bilingual report
        # We pass search_details if present for a more detailed AI report
        search_details = pricing_data.get('search_details')
        
        # 🆕 FIX 2: Ensure the generator receives the data it needs
        bilingual_report = self.report_generator.generate_complete_report(
            product_specs,  # Contains the dynamic web specs
            cv_output,      # Now contains the usage_years
            pricing_data, 
            search_details
        )
        
        return self._build_success_response(
            product_name, brand, model, product_type, usage_years,
            cv_output, product_specs, pricing_data, bilingual_report
        )

    def _parse_product_name(self, product_name: str) -> Tuple[str, str]:
        parts = product_name.split(maxsplit=1)
        return (parts[0], parts[1]) if len(parts) == 2 else (product_name, product_name)

    def _handle_price_not_found(self, product_name: str, cv_output: Dict) -> Dict:
        return {
            'success': False,
            'error': 'price_not_found',
            'message': f'Market price not found for {product_name}',
            'cv_analysis': cv_output
        }

    def _build_success_response(
        self, product_name, brand, model, product_type, usage_years,
        cv_output, product_specs, pricing_data, bilingual_report
    ) -> Dict:
        return {
            'success': True,
            'product_info': {
                'name': product_name, 'brand': brand, 'model': model,
                'type': product_type, 'usage_years': usage_years
            },
            'cv_analysis': cv_output,
            'product_specs': product_specs,
            'pricing': pricing_data,
            'report': {
                'english': bilingual_report.get('english'),
                'arabic': bilingual_report.get('arabic'),
                'full_text': bilingual_report.get('full_text')
            }
        }