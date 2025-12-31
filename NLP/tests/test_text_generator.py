import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.nlp_engine.text_generator import TextGenerator
from src.utils.config import Config

class TestTextGenerator(unittest.TestCase):
    """Test cases for text generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.text_generator = TextGenerator()
        self.mock_data = Config.load_mock_data()
    
    def test_generate_full_explanation_excellent_condition(self):
        """Test generation for excellent condition item"""
        cv_data = self.mock_data['examples'][0]
        pricing_data = {
            'reference_new_price': 5000.00,
            'calculated_used_price': 4500.00,
            'discount_percentage': 10,
            'price_factors': {
                'base_depreciation': 10,
                'condition_adjustment': 0,
                'issue_penalty': 0
            }
        }
        
        explanation = self.text_generator.generate_full_explanation(cv_data, pricing_data)
        
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 50)
        self.assertIn('excellent', explanation.lower())
    
    def test_generate_full_explanation_fair_condition(self):
        """Test generation for fair condition item"""
        cv_data = self.mock_data['examples'][2]
        pricing_data = {
            'reference_new_price': 1200.00,
            'calculated_used_price': 720.00,
            'discount_percentage': 40,
            'price_factors': {
                'base_depreciation': 30,
                'condition_adjustment': 10,
                'issue_penalty': 0
            }
        }
        
        explanation = self.text_generator.generate_full_explanation(cv_data, pricing_data)
        
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 50)
        self.assertIn('fair', explanation.lower())
    
    def test_generate_short_summary(self):
        """Test short summary generation"""
        cv_data = self.mock_data['examples'][1]
        pricing_data = {
            'reference_new_price': 999.00,
            'calculated_used_price': 699.30,
            'discount_percentage': 30
        }
        
        summary = self.text_generator.generate_short_summary(cv_data, pricing_data)
        
        self.assertIsInstance(summary, str)
        self.assertLess(len(summary), 200)
        self.assertIn('%', summary)
    
    def test_generate_bullet_points(self):
        """Test bullet point generation"""
        cv_data = self.mock_data['examples'][1]
        pricing_data = {
            'reference_new_price': 999.00,
            'calculated_used_price': 699.30,
            'discount_percentage': 30
        }
        
        bullets = self.text_generator.generate_bullet_points(cv_data, pricing_data)
        
        self.assertIsInstance(bullets, list)
        self.assertGreater(len(bullets), 0)
        self.assertTrue(all(isinstance(b, str) for b in bullets))
    
    def test_empty_issues(self):
        """Test handling of items with no issues"""
        cv_data = {
            'item_id': 'TEST001',
            'condition_score': 9.5,
            'detected_issues': [],
            'overall_condition': 'excellent'
        }
        pricing_data = {
            'reference_new_price': 1000.00,
            'calculated_used_price': 900.00,
            'discount_percentage': 10
        }
        
        explanation = self.text_generator.generate_full_explanation(cv_data, pricing_data)
        
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 30)

if __name__ == '__main__':
    unittest.main()