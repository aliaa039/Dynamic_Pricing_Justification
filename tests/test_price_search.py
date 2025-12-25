import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.external.price_search import PriceSearchEngine
from src.external.price_cache import PriceCache

class TestPriceSearch(unittest.TestCase):
    """Test cases for price search functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.search_engine = PriceSearchEngine()
        self.cache = PriceCache(cache_file='data/test_cache.json')
    
    def tearDown(self):
        """Clean up test cache"""
        if os.path.exists('data/test_cache.json'):
            os.remove('data/test_cache.json')
    
    def test_build_search_query(self):
        """Test search query construction"""
        query = self.search_engine._build_search_query('Canon', 'EOS 80D', 'camera')
        self.assertIn('Canon', query)
        self.assertIn('EOS 80D', query)
        self.assertIn('camera', query)
    
    def test_extract_price_from_text(self):
        """Test price extraction from text"""
        price = self.search_engine._extract_price_from_text('$1,299.99')
        self.assertEqual(price, 1299.99)
        
        price = self.search_engine._extract_price_from_text('Price: 599')
        self.assertEqual(price, 599.0)
        
        price = self.search_engine._extract_price_from_text('Invalid text')
        self.assertIsNone(price)
    
    def test_fallback_price(self):
        """Test fallback pricing"""
        result = self.search_engine._get_fallback_price('Canon', 'EOS 80D', 'camera')
        
        self.assertIsNotNone(result)
        self.assertIn('price', result)
        self.assertEqual(result['source'], 'Estimated')
        self.assertGreater(result['price'], 0)
    
    def test_validate_search_result(self):
        """Test result validation"""
        valid_result = {
            'price': 1000.00,
            'confidence': 0.8,
            'source': 'Test'
        }
        self.assertTrue(self.search_engine.validate_search_result(valid_result))
        
        invalid_result = {
            'price': -100,
            'confidence': 0.8
        }
        self.assertFalse(self.search_engine.validate_search_result(invalid_result))
        
        low_confidence = {
            'price': 1000,
            'confidence': 0.1
        }
        self.assertFalse(self.search_engine.validate_search_result(low_confidence))
    
    def test_cache_operations(self):
        """Test price caching"""
        price_data = {
            'price': 999.99,
            'source': 'Amazon',
            'confidence': 0.9
        }
        
        self.cache.set('Apple', 'iPhone 13', price_data)
        
        cached = self.cache.get('Apple', 'iPhone 13')
        self.assertIsNotNone(cached)
        self.assertEqual(cached['price'], 999.99)
        
        not_cached = self.cache.get('Samsung', 'Galaxy S21')
        self.assertIsNone(not_cached)
    
    def test_select_best_result(self):
        """Test best result selection"""
        results = [
            {'price': 1000, 'confidence': 0.7, 'source': 'A'},
            {'price': 1050, 'confidence': 0.9, 'source': 'B'},
            {'price': 980, 'confidence': 0.6, 'source': 'C'}
        ]
        
        best = self.search_engine._select_best_result(results)
        self.assertEqual(best['source'], 'B')
        self.assertEqual(best['confidence'], 0.9)

if __name__ == '__main__':
    unittest.main(verbosity=2)