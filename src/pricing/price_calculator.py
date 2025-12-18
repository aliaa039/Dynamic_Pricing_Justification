from src.data_processing.feature_extractor import FeatureExtractor
from src.utils.config import Config

class PriceCalculator:
    """Calculate used item price based on condition and market data"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
    
    def calculate_used_price(self, brand, model, cv_data, reference_price=None):
        """
        Calculate used price for an item
        This is a mock implementation - in production, you'd integrate with actual pricing API
        """
        if reference_price is None:
            reference_price = self._get_reference_price(brand, model)
        
        base_depreciation = self._calculate_base_depreciation(cv_data)
        condition_adjustment = self._calculate_condition_adjustment(cv_data)
        issue_penalty = self._calculate_issue_penalty(cv_data)
        
        total_depreciation = base_depreciation + condition_adjustment + issue_penalty
        total_depreciation = min(total_depreciation, 80)
        
        discount_percentage = round(total_depreciation, 2)
        used_price = reference_price * (1 - discount_percentage / 100)
        
        return {
            'reference_new_price': reference_price,
            'calculated_used_price': round(used_price, 2),
            'discount_percentage': discount_percentage,
            'price_factors': {
                'base_depreciation': base_depreciation,
                'condition_adjustment': condition_adjustment,
                'issue_penalty': issue_penalty
            }
        }
    
    def _get_reference_price(self, brand, model):
        """Mock function to get reference new price"""
        mock_prices = {
            'canon': 5000.00,
            'nikon': 4500.00,
            'sony': 5500.00,
            'apple': 999.00,
            'samsung': 899.00,
            'dell': 1200.00,
            'hp': 1100.00
        }
        
        brand_lower = brand.lower()
        return mock_prices.get(brand_lower, 1000.00)
    
    def _calculate_base_depreciation(self, cv_data):
        """Calculate base depreciation from condition score"""
        condition_score = cv_data.get('condition_score', 7.0)
        
        if condition_score >= 9:
            return 10
        elif condition_score >= 8:
            return 15
        elif condition_score >= 7:
            return 20
        elif condition_score >= 6:
            return 30
        elif condition_score >= 5:
            return 40
        else:
            return 50
    
    def _calculate_condition_adjustment(self, cv_data):
        """Adjust based on overall condition category"""
        condition_adjustments = {
            'excellent': 0,
            'good': 5,
            'fair': 10,
            'poor': 15
        }
        
        condition = cv_data.get('overall_condition', 'good')
        return condition_adjustments.get(condition, 5)
    
    def _calculate_issue_penalty(self, cv_data):
        """Calculate penalty based on detected issues"""
        issues = cv_data.get('detected_issues', [])
        
        if not issues:
            return 0
        
        total_penalty = 0
        
        for issue in issues:
            issue_type = issue.get('type', '')
            severity = issue.get('severity', 'minor')
            confidence = issue.get('confidence', 0.5)
            
            base_penalty = {
                'crack': 15,
                'dent': 10,
                'scratch': 5,
                'discoloration': 3,
                'wear': 2
            }.get(issue_type, 2)
            
            severity_multiplier = {
                'minor': 0.5,
                'moderate': 1.0,
                'severe': 2.0
            }.get(severity, 1.0)
            
            penalty = base_penalty * severity_multiplier * confidence
            total_penalty += penalty
        
        return min(total_penalty, 30)