import json
import os
from datetime import datetime
from typing import Dict, Optional

class PriceDatabase:
    """
    Local database for product prices
    Provides fast, accurate pricing for known products
    """
    
    def __init__(self, db_file='data/price_database.json'):
        self.db_file = db_file
        self.prices = self._load_database()
    
    def _load_database(self) -> Dict:
        """Load price database from file"""
        if not os.path.exists(self.db_file):
            return {}
        
        try:
            with open(self.db_file, 'r') as f:
                data = json.load(f)
                return data.get('products', {})
        except Exception as e:
            print(f"Error loading price database: {e}")
            return {}
    
    def _save_database(self):
        """Save price database to file"""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
        data = {
            'products': self.prices,
            'last_updated': datetime.now().isoformat(),
            'total_products': len(self.prices)
        }
        
        with open(self.db_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_key(self, brand: str, model: str) -> str:
        """Generate consistent key for product"""
        key = f"{brand}_{model}".lower()
        key = key.replace(' ', '_').replace('-', '_')
        return ''.join(c for c in key if c.isalnum() or c == '_')
    
    def get_price(self, brand: str, model: str) -> Optional[Dict]:
        """Get price for product from database"""
        key = self._generate_key(brand, model)
        
        if key in self.prices:
            product_data = self.prices[key]
            return {
                'price': product_data['price'],
                'source': f"Database ({product_data.get('source', 'Unknown')})",
                'confidence': 0.95,
                'currency': product_data.get('currency', 'USD'),
                'last_updated': product_data.get('last_updated'),
                'category': product_data.get('category')
            }
        
        return None
    
    def add_price(self, brand: str, model: str, price: float, 
                source: str = 'Manual', category: str = None):
        """Add or update price in database"""
        key = self._generate_key(brand, model)
        
        self.prices[key] = {
            'brand': brand,
            'model': model,
            'price': price,
            'category': category,
            'source': source,
            'last_updated': datetime.now().isoformat(),
            'currency': 'USD'
        }
        
        self._save_database()
    
    def delete_price(self, brand: str, model: str) -> bool:
        """Delete price from database"""
        key = self._generate_key(brand, model)
        
        if key in self.prices:
            del self.prices[key]
            self._save_database()
            return True
        
        return False
    
    def search_products(self, query: str) -> list:
        """Search products by brand or model"""
        query_lower = query.lower()
        results = []
        
        for key, product in self.prices.items():
            if (query_lower in product['brand'].lower() or 
                query_lower in product['model'].lower()):
                results.append(product)
        
        return results
    
    def list_all(self) -> Dict:
        """List all products in database"""
        return self.prices
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        categories = {}
        brands = {}
        
        for product in self.prices.values():
            category = product.get('category', 'Unknown')
            brand = product.get('brand', 'Unknown')
            
            categories[category] = categories.get(category, 0) + 1
            brands[brand] = brands.get(brand, 0) + 1
        
        return {
            'total_products': len(self.prices),
            'categories': categories,
            'brands': brands
        }