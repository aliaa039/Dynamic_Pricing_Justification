import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pricing.price_calculator import PriceCalculator
from src.nlp_engine.text_generator import TextGenerator
from src.utils.config import Config

class TestMockDataIntegration(unittest.TestCase):
    """Integration tests using mock CV data"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.price_calculator = PriceCalculator()
        self.text_generator = TextGenerator()
        self.mock_data = Config.load_mock_data()
    
    def test_camera_example(self):
        """Test with camera mock data"""
        cv_data = self.mock_data['examples'][0]
        
        pricing_data = self.price_calculator.calculate_used_price(
            'Canon', 'EOS 80D', cv_data
        )
        
        explanation = self.text_generator.generate_full_explanation(cv_data, pricing_data)
        
        print("\n=== CAMERA EXAMPLE ===")
        print(f"Condition: {cv_data['overall_condition']}")
        print(f"Score: {cv_data['condition_score']}")
        print(f"Original Price: ${pricing_data['reference_new_price']}")
        print(f"Used Price: ${pricing_data['calculated_used_price']}")
        print(f"Discount: {pricing_data['discount_percentage']}%")
        print(f"\nExplanation:\n{explanation}")
        
        self.assertIsNotNone(explanation)
        self.assertGreater(pricing_data['calculated_used_price'], 0)
    
    def test_phone_example(self):
        """Test with phone mock data"""
        cv_data = self.mock_data['examples'][1]
        
        pricing_data = self.price_calculator.calculate_used_price(
            'Apple', 'iPhone 13', cv_data
        )
        
        explanation = self.text_generator.generate_full_explanation(cv_data, pricing_data)
        
        print("\n=== PHONE EXAMPLE ===")
        print(f"Condition: {cv_data['overall_condition']}")
        print(f"Score: {cv_data['condition_score']}")
        print(f"Original Price: ${pricing_data['reference_new_price']}")
        print(f"Used Price: ${pricing_data['calculated_used_price']}")
        print(f"Discount: {pricing_data['discount_percentage']}%")
        print(f"\nExplanation:\n{explanation}")
        
        self.assertIsNotNone(explanation)
    
    def test_laptop_example(self):
        """Test with laptop mock data"""
        cv_data = self.mock_data['examples'][2]
        
        pricing_data = self.price_calculator.calculate_used_price(
            'Dell', 'XPS 15', cv_data
        )
        
        explanation = self.text_generator.generate_full_explanation(cv_data, pricing_data)
        
        print("\n=== LAPTOP EXAMPLE ===")
        print(f"Condition: {cv_data['overall_condition']}")
        print(f"Score: {cv_data['condition_score']}")
        print(f"Original Price: ${pricing_data['reference_new_price']}")
        print(f"Used Price: ${pricing_data['calculated_used_price']}")
        print(f"Discount: {pricing_data['discount_percentage']}%")
        print(f"\nExplanation:\n{explanation}")
        
        self.assertIsNotNone(explanation)
    
    def test_all_formats(self):
        """Test all output formats"""
        cv_data = self.mock_data['examples'][1]
        
        pricing_data = self.price_calculator.calculate_used_price(
            'Samsung', 'Galaxy S21', cv_data
        )
        
        print("\n=== ALL FORMATS TEST ===")
        
        full = self.text_generator.generate_full_explanation(cv_data, pricing_data)
        print(f"\nFull Format:\n{full}")
        
        short = self.text_generator.generate_short_summary(cv_data, pricing_data)
        print(f"\nShort Format:\n{short}")
        
        bullets = self.text_generator.generate_bullet_points(cv_data, pricing_data)
        print(f"\nBullet Format:")
        for bullet in bullets:
            print(f"  • {bullet}")
        
        self.assertIsNotNone(full)
        self.assertIsNotNone(short)
        self.assertIsInstance(bullets, list)

if __name__ == '__main__':
    unittest.main(verbosity=2)