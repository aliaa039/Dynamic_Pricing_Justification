import os
import sys
from flask import Flask, request, jsonify

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    from src.data_processing.input_validator import InputValidator
    from src.nlp_engine.text_generator import TextGenerator
    from src.nlp_engine.llm_report_generator import LLMReportGenerator
    from src.pricing.price_calculator import PriceCalculator
    from src.pricing.discount_explainer import DiscountExplainer
    print("✅ All modules imported successfully!")
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    sys.exit(1)

app = Flask(__name__)

text_generator = TextGenerator()
llm_generator = LLMReportGenerator()
SERP_KEY = os.getenv('SERPAPI_KEY', "84fe30f2dd187c0e37fce6d2397a53d442ceded2cf3c94434facdc1c8b6dcfa2")
price_calculator = PriceCalculator(use_web_search=True, serpapi_key=SERP_KEY)
discount_explainer = DiscountExplainer()
validator = InputValidator()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'dynamic-pricing-nlp',
        'features': ['price_search', 'llm_reports', 'cv_analysis']
    })

@app.route('/calculate-price', methods=['POST'])
def calculate_price():
    """
    Calculate used price with full search details
    Returns detailed breakdown including market research
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        brand = data.get('brand')
        model = data.get('model')
        cv_output = data.get('cv_output')
        manual_price = data.get('reference_price')
        category = data.get('category')

        if not all([brand, model, cv_output]):
            return jsonify({'error': 'brand, model, and cv_output are required'}), 400

        print(f"\n{'='*60}")
        print(f"📱 Processing: {brand} {model}")
        print(f"{'='*60}")

        pricing_data = price_calculator.calculate_used_price(
            brand, model, cv_output, reference_price=manual_price, category=category
        )

        if pricing_data is None:
            print(f"❌ No price found for {brand} {model}")
            return jsonify({
                'status': 'price_not_found',
                'message': f"Could not find market price for '{brand} {model}'.",
                'instruction': "Please provide 'reference_price' manually to continue.",
                'searched_product': f"{brand} {model}"
            }), 404

        print(f"✅ Price calculated successfully")
        print(f"   New: EGP {pricing_data['reference_new_price']:,.2f}")
        print(f"   Used: EGP {pricing_data['calculated_used_price']:,.2f}")
        print(f"   Source: {pricing_data['price_metadata']['source']}")
        
        if 'search_details' in pricing_data:
            print(f"   Stores: {len(pricing_data['search_details']['stores_found'])} found")

        return jsonify(pricing_data), 200

    except Exception as e:
        print(f"🔥 Error in calculate_price: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/generate-report', methods=['POST'])
def generate_report():
    """
    Generate full pricing report with LLM
    This is the complete workflow: CV → Price → LLM Report
    """
    try:
        data = request.json
        cv_output = data.get('cv_output')
        brand = data.get('brand', 'Unknown')
        model = data.get('model', 'Unknown')
        manual_price = data.get('reference_price')
        category = data.get('category')
        use_llm = data.get('use_llm', True)

        if not cv_output:
            return jsonify({'error': 'cv_output is required'}), 400

        print(f"\n{'='*60}")
        print(f"📄 Generating Report: {brand} {model}")
        print(f"{'='*60}")

        # Step 1: Calculate pricing
        print("Step 1: Calculating prices...")
        pricing_data = price_calculator.calculate_used_price(
            brand, model, cv_output, reference_price=manual_price, category=category
        )

        if pricing_data is None:
            return jsonify({
                'status': 'price_required',
                'message': 'No market price found. Provide reference_price to continue.'
            }), 404

        print(f"✅ Pricing complete: EGP {pricing_data['calculated_used_price']:,.2f}")

        # Step 2: Generate report with LLM or templates
        print(f"Step 2: Generating {'LLM' if use_llm else 'template'} report...")
        
        if use_llm:
            search_details = pricing_data.get('search_details')
            report = llm_generator.generate_pricing_report(
                cv_output, pricing_data, search_details
            )
        else:
            report = text_generator.generate_full_explanation(cv_output, pricing_data)

        print("✅ Report generated successfully")

        response = {
            'report': report,
            'pricing': pricing_data,
            'condition_summary': {
                'overall': cv_output.get('overall_condition'),
                'score': cv_output.get('condition_score'),
                'issues': len(cv_output.get('detected_issues', []))
            },
            'metadata': {
                'brand': brand,
                'model': model,
                'report_type': 'llm' if use_llm else 'template'
            }
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"🔥 Error in generate_report: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/search-price', methods=['POST'])
def search_price():
    """
    Search for product price only (no calculation)
    Useful for checking market prices before listing
    """
    try:
        data = request.json
        brand = data.get('brand')
        model = data.get('model')
        category = data.get('category')

        if not all([brand, model]):
            return jsonify({'error': 'brand and model are required'}), 400

        print(f"\n🔍 Searching price for: {brand} {model}")

        from src.external.price_search import PriceSearchEngine
        search_engine = PriceSearchEngine(api_key=SERP_KEY)
        
        result = search_engine.search_product_price(brand, model, category)

        if search_engine.validate_search_result(result):
            print(f"✅ Found: EGP {result['price']:,.2f}")
            return jsonify(result), 200
        else:
            print(f"❌ No results found")
            return jsonify({
                'status': 'not_found',
                'message': f"No market price found for '{brand} {model}'",
                'searched_product': f"{brand} {model}"
            }), 404

    except Exception as e:
        print(f"🔥 Error in search_price: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 DYNAMIC PRICING SERVER STARTING")
    print(f"📍 Host: http://127.0.0.1:5000")
    print(f"📚 Endpoints:")
    print(f"   - POST /calculate-price")
    print(f"   - POST /generate-report (with LLM)")
    print(f"   - POST /search-price")
    print(f"   - GET  /health")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)