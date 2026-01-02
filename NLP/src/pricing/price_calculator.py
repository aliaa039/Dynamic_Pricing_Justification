import os
from src.external.price_search import PriceSearchEngine
from src.external.price_cache import PriceCache
from src.external.price_database import PriceDatabase

class PriceCalculator:
    """
    Calculates fair used price based on condition, usage, and market data.
    Integrates with condition evaluator for accurate damage assessment.
    """
    
    def __init__(self, use_web_search=True, serpapi_key=None):
        self.use_web_search = use_web_search
        self.price_db = PriceDatabase()
        
        if use_web_search:
            api_key = serpapi_key or os.getenv('SERPAPI_KEY')
            self.price_search = PriceSearchEngine(api_key=api_key)
            self.price_cache = PriceCache()
    
    def calculate_used_price(self, brand, model, cv_data, reference_price=None, category=None):
        """
        Calculate used price by applying depreciation to reference price.
        """
        # Get reference price if not provided
        if reference_price is None:
            reference_data = self._get_reference_price(brand, model, category)
            if not reference_data or reference_data.get('price') is None:
                return None
            
            reference_price = reference_data['price']
            price_source = reference_data.get('source', 'unknown')
        else:
            price_source = 'manual'
        
        # Calculate depreciation components
        usage_depreciation = self._calculate_usage_depreciation(cv_data)
        condition_depreciation = self._calculate_condition_depreciation(cv_data)
        damage_depreciation = self._calculate_damage_depreciation(cv_data)
        
        # Total depreciation (capped at 85% to maintain minimum value)
        total_depreciation = min(
            usage_depreciation + condition_depreciation + damage_depreciation,
            85.0
        )
        
        # Calculate final price
        used_price = reference_price * (1 - total_depreciation / 100)
        
        # Build detailed response
        return {
            'reference_new_price': reference_price,
            'calculated_used_price': round(used_price, 2),
            'discount_percentage': round(total_depreciation, 2),
            'discount_breakdown': {
                'usage': round(usage_depreciation, 2),
                'condition': round(condition_depreciation, 2),
                'damage': round(damage_depreciation, 2)
            },
            'currency': 'EGP',
            'price_metadata': {
                'brand': brand,
                'model': model,
                'source': price_source,
                'condition_score': cv_data.get('condition_score', 7.0),
                'issues_count': cv_data.get('issues_count', 0)
            }
        }
    
    def _get_reference_price(self, brand, model, category):
        """
        Get reference price with fallback strategy:
        1. Try database first
        2. Try cache (using corrected 'get' method)
        3. Try web search
        """
        # 1. Try database
        db_price = self.price_db.get_price(brand, model)
        if db_price and db_price.get('price'):
            return {
                'price': db_price['price'],
                'source': 'database'
            }
        
        # 2. Try Cache and Web Search
        if self.use_web_search and hasattr(self, 'price_search'):
            
            # ✅ FIXED: Using 'get' instead of 'get_price' to match PriceCache
            if hasattr(self, 'price_cache'):
                cached_data = self.price_cache.get(brand, model, category)
                if cached_data:
                    # Extract price if the cache returns a dictionary/object
                    price_val = cached_data.get('price') if isinstance(cached_data, dict) else cached_data
                    return {
                        'price': price_val,
                        'source': 'cache'
                    }
            
            # 3. Search web (triggered if not in DB or Cache)
            search_result = self.price_search.search_product_price(brand, model, category)
            
            if search_result and search_result.get('price'):
                # ✅ FIXED: Using 'set' instead of 'save_price' to match PriceCache
                if hasattr(self, 'price_cache'):
                    self.price_cache.set(brand, model, search_result, category)
                
                return {
                    'price': search_result['price'],
                    'source': 'web_search'
                }
        
        return None
    
    def _calculate_usage_depreciation(self, cv_data):
        """Calculate depreciation based on usage duration (years)"""
        usage_years = cv_data.get('usage_years', 1.0)
        
        if usage_years < 0.5:
            return 10.0
        elif usage_years < 1.0:
            return 15.0
        elif usage_years < 2.0:
            return 25.0
        elif usage_years < 3.0:
            return 35.0
        else:
            return 45.0
    
    def _calculate_condition_depreciation(self, cv_data):
        """Calculate depreciation based on overall condition label"""
        condition = cv_data.get('overall_condition', 'good').lower()
        
        condition_map = {
            'excellent': 0.0,
            'very good': 2.0,
            'good': 5.0,
            'fair': 10.0,
            'poor': 15.0,
            'damaged': 20.0,
            'broken': 30.0
        }
        return condition_map.get(condition, 5.0)
    
    def _calculate_damage_depreciation(self, cv_data):
        """Calculate impact from specific detected physical issues"""
        damage_impact = cv_data.get('total_discount_impact', 0.0)
        damage_percentage = damage_impact * 100
        
        # Fallback if impact is not pre-calculated
        detected_issues = cv_data.get('detected_issues', [])
        if damage_percentage == 0.0 and detected_issues:
            severity_weights = {
                'minor': 2.0, 'moderate': 5.0, 'severe': 10.0, 'critical': 15.0
            }
            total = sum(severity_weights.get(i.get('severity', 'minor'), 2.0) for i in detected_issues)
            damage_percentage = min(total, 25.0)
        
        return damage_percentage

    def get_price_explanation(self, pricing_result: dict) -> str:
        """Generate human-readable breakdown for the UI report"""
        if not pricing_result:
            return "Pricing calculation failed."
        
        breakdown = pricing_result.get('discount_breakdown', {})
        parts = []
        if breakdown.get('usage', 0) > 0:
            parts.append(f"{breakdown['usage']:.0f}% for age")
        if breakdown.get('condition', 0) > 0:
            parts.append(f"{breakdown['condition']:.0f}% for condition")
        if breakdown.get('damage', 0) > 0:
            parts.append(f"{breakdown['damage']:.0f}% for physical damage")
        
        explanation = "Breakdown: " + ", ".join(parts)
        explanation += f". Total discount: {pricing_result.get('discount_percentage', 0):.0f}%"
        return explanation