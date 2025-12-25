import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

class PriceCache:
    """
    Cache for searched prices to avoid repeated web requests
    Reduces load and improves response time
    """
    
    def __init__(self, cache_file='data/price_cache.json', expiry_days=7):
        self.cache_file = cache_file
        self.expiry_days = expiry_days
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from file"""
        if not os.path.exists(self.cache_file):
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_cache(self):
        """Save cache to file"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _generate_key(self, brand: str, model: str, category: str = None) -> str:
        """Generate unique cache key"""
        key = f"{brand.lower()}_{model.lower()}"
        if category:
            key += f"_{category.lower()}"
        return key.replace(' ', '_')
    
    def get(self, brand: str, model: str, category: str = None) -> Optional[Dict]:
        """Get cached price if available and not expired"""
        key = self._generate_key(brand, model, category)
        
        if key not in self.cache:
            return None
        
        cached_data = self.cache[key]
        cached_time = datetime.fromisoformat(cached_data['timestamp'])
        
        if datetime.now() - cached_time > timedelta(days=self.expiry_days):
            del self.cache[key]
            self._save_cache()
            return None
        
        return cached_data['price_data']
    
    def set(self, brand: str, model: str, price_data: Dict, category: str = None):
        """Cache price data"""
        key = self._generate_key(brand, model, category)
        
        self.cache[key] = {
            'timestamp': datetime.now().isoformat(),
            'price_data': price_data
        }
        
        self._save_cache()
    
    def clear_expired(self):
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = []
        
        for key, data in self.cache.items():
            cached_time = datetime.fromisoformat(data['timestamp'])
            if now - cached_time > timedelta(days=self.expiry_days):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self._save_cache()
    
    def clear_all(self):
        """Clear entire cache"""
        self.cache = {}
        self._save_cache()