from typing import List, Dict, Optional
from serpapi import GoogleSearch
import re
import os

class PriceSearchEngine:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        self.egyptian_sites = [
            "jumia.com.eg", "noon.com/egypt", "dubaiphone.net","egyptlaptop.com", "cairosales.com",
            "dream2000.com", "b.tech", "xcite.com", "souq.com","elarabygroup.com","2b.com.eg"
        ]
        self.used_keywords = ["used", "refurbished", "مستعمل", "مجدد", "open box", "renewed"]

    def search_product_price(self, brand: str, model: str, category: str = None) -> Dict:
        """Main entry point for PriceCalculator"""
        query = f"{brand} {model}"
        raw_results = self.search_product(query)
        processed = self.process_results(raw_results, query)
        return self.create_report(query, processed)

    def search_product(self, product: str) -> List[Dict]:
        """Search Egyptian sites via SerpAPI"""
        if not self.api_key:
            return []
        
        site_query = " OR ".join([f"site:{site}" for site in self.egyptian_sites])
        params = {
            "engine": "google",
            "q": f'"{product}" NEW price Egypt {site_query} -used -مستعمل',
            "location": "Cairo, Egypt",
            "hl": "en",
            "num": 30,
            "api_key": self.api_key
        }
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict().get("organic_results", [])
            print(f"[SEARCH] Found {len(results)} raw results for: {product}")
            return results
        except Exception as e:
            print(f"[SEARCH ERROR] {e}")
            return []

    def process_results(self, results: List[Dict], product: str) -> List[Dict]:
        """Filter and extract prices from search results"""
        processed = []
        
        for r in results:
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            link = r.get("link", "")
            
            # Filter used/refurbished
            text = f"{title} {snippet}".lower()
            if any(k in text for k in self.used_keywords):
                continue
            
            # Extract price
            price = self.extract_price(f"{title} {snippet}")
            if not price:
                continue
            
            # Extract store
            store = self.extract_store(link)
            
            processed.append({
                "title": title,
                "store": store,
                "price": price,
                "url": link
            })
        
        # Sort by price (cheapest first)
        processed = sorted(processed, key=lambda x: x["price"])
        
        print(f"[PROCESS] Extracted {len(processed)} valid prices")
        if processed:
            print(f"[PROCESS] Price range: EGP {processed[0]['price']:,.0f} - {processed[-1]['price']:,.0f}")
        
        return processed

    def extract_price(self, text: str) -> Optional[float]:
        """Extract Egyptian pound prices from text"""
        text_lower = text.lower()
        
        # Words that indicate this number is NOT a price
        invalid_context = ["star", "rating", "review", "piece", "item", "year", 
                        "warranty", "month", "قسط", "شهور"]
        
        # Patterns that must have currency symbols
        patterns = [
            r'(?:EGP|LE|ج\.م|جنيه)\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'([0-9,]+(?:\.[0-9]{2})?)\s*(?:EGP|LE|ج\.م|جنيه)'
        ]
        
        found_prices = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price_str = match.group(1).replace(',', '')
                    price_val = float(price_str)
                    
                    # Get context around the price
                    start, end = match.span()
                    context = text_lower[max(0, start-20):min(len(text_lower), end+20)]
                    
                    # Skip if context has invalid words
                    if any(word in context for word in invalid_context):
                        continue
                    
                    # Price must be reasonable (100 - 200,000 EGP)
                    if price_val < 100 or price_val > 200000:
                        continue
                    
                    found_prices.append(price_val)
                except:
                    continue
        
        if not found_prices:
            return None
        
        # Return the highest valid price found (usually the actual product price)
        return max(found_prices)

    def extract_store(self, url: str) -> str:
        """Extract store name from URL"""
        store_map = {
            "jumia": "Jumia Egypt",
            "noon": "Noon",
            "b.tech": "B.TECH",
            "dream2000": "Dream 2000",
            "dubaiphone": "Dubai Phone",
            "xcite": "Xcite",
            "souq": "Souq"
        }
        
        url_lower = url.lower()
        for key, name in store_map.items():
            if key in url_lower:
                return name
        
        return "Egyptian Retailer"

    def create_report(self, product: str, results: List[Dict]) -> Dict:
        """
        Build the dictionary that PriceCalculator expects
        IMPORTANT: Must return 'results' array for search_details to work!
        """
        if not results:
            print(f"[REPORT] No results found for: {product}")
            return {
                "price": None,
                "source": "Not Found",
                "confidence": 0.0,
                "total_results": 0,
                "results": []  # Empty but present
            }
        
        prices = [r["price"] for r in results]
        min_price = min(prices)
        max_price = max(prices)
        median_price = sorted(prices)[len(prices)//2]
        
        print(f"[REPORT] Success! {len(results)} results")
        print(f"[REPORT] Best price: EGP {min_price:,.2f} at {results[0]['store']}")
        
        return {
            "price": median_price,  # Return median price
            "source": f"Egyptian Store ({results[0]['store']})",
            "confidence": 0.85,
            "currency": "EGP",
            "total_results": len(results),
            "results": results,  # ✅ CRITICAL: Include full results array
            "price_statistics": {
                "min": min_price,
                "max": max_price,
                "median": (median_price)
            }
        }

    def validate_search_result(self, result: Dict) -> bool:
        """Check if search result is valid"""
        return result.get("price") is not None and result.get("price") > 0