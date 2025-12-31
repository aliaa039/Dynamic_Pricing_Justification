import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    from src.data_processing.input_validator import InputValidator
    from src.nlp_engine.text_generator import TextGenerator
    from src.nlp_engine.bilingual_report_generator import BilingualReportGenerator
    from src.pricing.price_calculator import PriceCalculator
    from src.pricing.discount_explainer import DiscountExplainer
    from src.external.product_specs_extractor import ProductSpecsExtractor
    from src.services.cv_integration_service import CVIntegrationService  # 🆕 NEW
    print("✅ All modules imported successfully!")
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

app = Flask(__name__)
CORS(app)

text_generator = TextGenerator()
bilingual_generator = BilingualReportGenerator()
specs_extractor = ProductSpecsExtractor()

SERP_KEY = os.getenv('SERPAPI_KEY', "your-key-here")
price_calculator = PriceCalculator(use_web_search=True, serpapi_key=SERP_KEY)
discount_explainer = DiscountExplainer()
validator = InputValidator()

# 🆕 NEW - Initialize CV Integration Service
# OLD CODE (Causing the error)
# ✅ New code (the class now loads keys internally via os.getenv)
cv_service = CVIntegrationService()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'dynamic-pricing-nlp',
        'features': ['cv_integration', 'price_search', 'specs_extraction', 'bilingual_reports']
    })

@app.route('/cv-to-pricing', methods=['POST'])
def cv_to_pricing():
    """
    COMPLETE WORKFLOW: CV Analysis → Pricing → Bilingual Report
    This is the main integration endpoint for Streamlit CV app
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        # Extract required fields
        product_name = data.get('product_name')
        product_type = data.get('product_type')
        usage_years = data.get('usage_years', 0)
        analysis_results = data.get('analysis_results', {})
        
        if not all([product_name, product_type, analysis_results]):
            return jsonify({
                'error': 'Required fields: product_name, product_type, analysis_results'
            }), 400

        # 🆕 NEW - Use Service Layer instead of inline logic
        result = cv_service.process_complete_workflow(
            product_name=product_name,
            product_type=product_type,
            usage_years=usage_years,
            gemini_analysis=analysis_results
        )
        
        # Return response with appropriate status code
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code

    except Exception as e:
        print(f"🔥 Error in cv_to_pricing: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ... (keep all other endpoints unchanged)

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 DYNAMIC PRICING SERVER - WITH CV INTEGRATION")
    print(f"📍 Host: http://127.0.0.1:5000")
    print(f"📚 Endpoints:")
    print(f"   - POST /cv-to-pricing       (CV Integration - MAIN)")
    print(f"   - POST /calculate-price     (Price calculation)")
    print(f"   - POST /generate-report     (Bilingual report)")
    print(f"   - POST /extract-specs       (Product specs)")
    print(f"   - POST /search-price        (Price search)")
    print(f"   - GET  /health              (Health check)")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)