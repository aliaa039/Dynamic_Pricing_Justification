from flask import Flask, request, jsonify
from src.data_processing.input_validator import InputValidator
from src.nlp_engine.text_generator import TextGenerator
from src.pricing.price_calculator import PriceCalculator
from src.pricing.discount_explainer import DiscountExplainer

app = Flask(__name__)

text_generator = TextGenerator()
price_calculator = PriceCalculator()
discount_explainer = DiscountExplainer()
validator = InputValidator()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'dynamic-pricing-nlp'})

@app.route('/generate-explanation', methods=['POST'])
def generate_explanation():
    """
    Main endpoint to generate price explanation
    
    Expected input:
    {
        "cv_output": {...},
        "pricing_data": {...} (optional, will be calculated if not provided),
        "brand": "Canon",
        "model": "EOS 80D",
        "format": "full" | "short" | "bullets"
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        cv_output = data.get('cv_output')
        if not cv_output:
            return jsonify({'error': 'cv_output is required'}), 400
        
        cv_validation = validator.validate_cv_output(cv_output)
        if not cv_validation['valid']:
            return jsonify({
                'error': 'Invalid CV output',
                'details': cv_validation['errors']
            }), 400
        
        pricing_data = data.get('pricing_data')
        
        if not pricing_data:
            brand = data.get('brand', 'Unknown')
            model = data.get('model', 'Unknown')
            reference_price = data.get('reference_price')
            
            pricing_data = price_calculator.calculate_used_price(
                brand, model, cv_output, reference_price
            )
        else:
            pricing_validation = validator.validate_pricing_data(pricing_data)
            if not pricing_validation['valid']:
                return jsonify({
                    'error': 'Invalid pricing data',
                    'details': pricing_validation['errors']
                }), 400
        
        output_format = data.get('format', 'full')
        
        if output_format == 'short':
            explanation = text_generator.generate_short_summary(cv_output, pricing_data)
        elif output_format == 'bullets':
            explanation = text_generator.generate_bullet_points(cv_output, pricing_data)
        else:
            explanation = text_generator.generate_full_explanation(cv_output, pricing_data)
        
        discount_breakdown = discount_explainer.explain_discount_breakdown(
            pricing_data.get('price_factors', {})
        )
        
        value_proposition = discount_explainer.get_value_proposition(
            pricing_data.get('discount_percentage', 0)
        )
        
        response = {
            'explanation': explanation,
            'pricing': {
                'original_price': pricing_data.get('reference_new_price'),
                'used_price': pricing_data.get('calculated_used_price'),
                'discount_percentage': pricing_data.get('discount_percentage'),
                'discount_breakdown': discount_breakdown
            },
            'value_proposition': value_proposition,
            'condition_summary': {
                'overall': cv_output.get('overall_condition'),
                'score': cv_output.get('condition_score'),
                'issue_count': len(cv_output.get('detected_issues', []))
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/validate-cv-output', methods=['POST'])
def validate_cv():
    """Endpoint to validate CV output structure"""
    try:
        cv_output = request.json
        validation_result = validator.validate_cv_output(cv_output)
        
        return jsonify(validation_result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/calculate-price', methods=['POST'])
def calculate_price():
    """Endpoint to calculate price from brand, model, and CV output"""
    try:
        data = request.json
        
        brand = data.get('brand')
        model = data.get('model')
        cv_output = data.get('cv_output')
        reference_price = data.get('reference_price')
        
        if not all([brand, model, cv_output]):
            return jsonify({'error': 'brand, model, and cv_output are required'}), 400
        
        pricing_data = price_calculator.calculate_used_price(
            brand, model, cv_output, reference_price
        )
        
        return jsonify(pricing_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)