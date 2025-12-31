import os
from src.external.price_search import PriceSearchEngine
from src.external.price_cache import PriceCache
from src.external.price_database import PriceDatabase

class PriceCalculator:
    def __init__(self, use_web_search=True, serpapi_key=None):
        self.use_web_search = use_web_search
        self.price_db = PriceDatabase()
        if use_web_search:
            api_key = serpapi_key or os.getenv('SERPAPI_KEY')
            self.price_search = PriceSearchEngine(api_key=api_key)
            self.price_cache = PriceCache()

    def calculate_used_price(self, brand, model, cv_data, reference_price=None, category=None):
        """
        Calculate used price with full search details
        Returns None if no price found and user didn't provide one
        """
        search_details = None
        
        if reference_price is None:
            reference_data = self._get_reference_price(brand, model, category)
            
            if not reference_data or reference_data.get('price') is None:
                return None 
                
            reference_price = reference_data['price']
            price_source = reference_data.get('source', 'Web Search')
            
            # ✅ FIXED: Include search details in response
            results_list = reference_data.get('results', [])
            
            if results_list:
                prices = [r['price'] for r in results_list]
                stores = list(set([r['store'] for r in results_list]))
                
                search_details = {
                    'total_results': len(results_list),
                    'stores_found': stores,
                    'price_range': {
                        'min': min(prices),
                        'max': max(prices),
                        'average': round(sum(prices) / len(prices), 2)
                    },
                    'best_deal': {
                        'store': results_list[0]['store'],
                        'price': results_list[0]['price'],
                        'url': results_list[0].get('url', ''),
                        'title': results_list[0].get('title', '')
                    },
                    'all_offers': results_list[:5]  # Top 5 offers
                }
            else:
                search_details = {
                    'total_results': 0,
                    'stores_found': [],
                    'price_range': {'min': None, 'max': None, 'average': None},
                    'best_deal': None,
                    'all_offers': []
                }
        else:
            price_source = 'User Provided'
            search_details = None

        base_depreciation = self._calculate_base_depreciation(cv_data)
        condition_adjustment = self._calculate_condition_adjustment(cv_data)
        issue_penalty = self._calculate_issue_penalty(cv_data)
        
        total_depreciation = min(base_depreciation + condition_adjustment + issue_penalty, 80)
        used_price = reference_price * (1 - total_depreciation / 100)
        
        result = {
            'reference_new_price': reference_price,
            'calculated_used_price': round(used_price, 2),
            'discount_percentage': round(total_depreciation, 2),
            'price_factors': {
                'base_depreciation': base_depreciation,
                'condition_adjustment': condition_adjustment,
                'issue_penalty': issue_penalty
            },
            'price_metadata': {
                'source': price_source,
                'brand': brand,
                'model': model,
                'category': category,
                'currency': 'EGP'
            }
        }
        
        # ✅ FIXED: Add search details if available
        if search_details:
            result['search_details'] = search_details
        
        return result

    def _get_reference_price(self, brand, model, category=None):
        """
        Complete price lookup with proper priority:
        1. Database (instant)
        2. Cache (instant)
        3. Web Search (2-3s)
        4. None (no fallback)
        """
        # ✅ FIXED: Check database first
        db_price = self.price_db.get_price(brand, model)
        if db_price:
            print(f"✅ Price found in DATABASE: {brand} {model}")
            return db_price
        
        if not self.use_web_search:
            print(f"⚠️  Web search disabled, no price found")
            return None
        
        # ✅ FIXED: Check cache before searching
        cached_price = self.price_cache.get(brand, model, category)
        if cached_price:
            print(f"✅ Price found in CACHE: {brand} {model}")
            cached_price['source'] = f"{cached_price['source']} (Cached)"
            return cached_price
        
        # Search web
        print(f"🔍 Searching web for: {brand} {model}")
        search_result = self.price_search.search_product_price(brand, model, category)
        
        if self.price_search.validate_search_result(search_result):
            print(f"✅ Price found on WEB: EGP {search_result['price']}")
            
            # ✅ FIXED: Cache the result
            self.price_cache.set(brand, model, search_result, category)
            
            return search_result
        
        print(f"❌ No price found for: {brand} {model}")
        return None

    def _calculate_base_depreciation(self, cv_data):
        """Calculate depreciation based on condition score"""
        score = cv_data.get('condition_score', 7)
        if score >= 9: return 10
        if score >= 8: return 15
        if score >= 7: return 20
        if score >= 6: return 30
        return 40

    def _calculate_condition_adjustment(self, cv_data):
        """Adjust based on overall condition category"""
        condition_map = {
            'excellent': 0,
            'good': 5,
            'fair': 10,
            'poor': 15
        }
        return condition_map.get(cv_data.get('overall_condition', 'good'), 5)

    def _calculate_issue_penalty(self, cv_data):
        """Calculate penalty for detected issues"""
        issues = cv_data.get('detected_issues', [])
        if not issues:
            return 0
        
        total_penalty = 0
        for issue in issues:
            severity = issue.get('severity', 'minor')
            severity_map = {'minor': 2, 'moderate': 5, 'severe': 10}
            total_penalty += severity_map.get(severity, 2)
        
        return min(total_penalty, 30)