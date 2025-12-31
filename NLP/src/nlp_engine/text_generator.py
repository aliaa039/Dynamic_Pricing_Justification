from src.nlp_engine.template_manager import TemplateManager
from src.data_processing.feature_extractor import FeatureExtractor

class TextGenerator:
    """Generate natural language explanations for pricing"""
    
    def __init__(self):
        self.template_manager = TemplateManager()
        self.feature_extractor = FeatureExtractor()
    
    def generate_full_explanation(self, cv_data, pricing_data):
        """Generate complete price justification text"""
        opening = self._generate_opening(cv_data)
        issue_description = self._generate_issue_description(cv_data)
        price_justification = self._generate_price_justification(cv_data, pricing_data)
        closing = self._generate_closing(pricing_data)
        
        sections = [s for s in [opening, issue_description, price_justification, closing] if s]
        
        return " ".join(sections)
    
    def _generate_opening(self, cv_data):
        """Generate opening statement about overall condition"""
        condition = cv_data.get('overall_condition', 'good')
        return self.template_manager.get_condition_opening(condition)
    
    def _generate_issue_description(self, cv_data):
        """Generate description of detected issues"""
        priority_issues = self.feature_extractor.prioritize_issues(cv_data, max_issues=3)
        
        if not priority_issues:
            return ""
        
        issues_text = self.template_manager.format_multiple_issues(priority_issues)
        
        severity_dist = self.feature_extractor._analyze_severity_distribution(cv_data)
        
        if severity_dist['severe'] > 0:
            prefix = "Notable defects include"
        elif severity_dist['moderate'] > 0:
            prefix = "The item shows"
        else:
            prefix = "Minor imperfections include"
        
        return f"{prefix} {issues_text}."
    
    def _generate_price_justification(self, cv_data, pricing_data):
        """Generate justification for the price"""
        discount = pricing_data.get('discount_percentage', 0)
        used_price = pricing_data.get('calculated_used_price', 0)
        new_price = pricing_data.get('reference_new_price', 0)
        
        discount_explanation = self.template_manager.get_discount_explanation(discount)
        
        used_price_formatted = self.template_manager.format_price(used_price)
        new_price_formatted = self.template_manager.format_price(new_price)
        discount_formatted = self.template_manager.format_percentage(discount)
        
        justification = (
            f"{discount_explanation}, with the price reduced to {used_price_formatted} "
            f"({discount_formatted} off the original {new_price_formatted})"
        )
        
        return justification + "."
    
    def _generate_closing(self, pricing_data):
        """Generate positive closing statement"""
        discount = pricing_data.get('discount_percentage', 0)
        
        if discount > 25:
            return self.template_manager.get_positive_closing().capitalize() + "."
        
        return ""
    
    def generate_short_summary(self, cv_data, pricing_data):
        """Generate brief one-sentence summary"""
        condition = cv_data.get('overall_condition', 'good')
        discount = pricing_data.get('discount_percentage', 0)
        discount_formatted = self.template_manager.format_percentage(discount)
        
        most_critical = self.feature_extractor._get_most_critical_issue(cv_data)
        
        if most_critical:
            issue_desc = self.template_manager.format_issue_description(most_critical)
            return f"{condition.capitalize()} condition with {issue_desc}. Priced {discount_formatted} below retail."
        else:
            return f"{condition.capitalize()} condition. Priced {discount_formatted} below retail."
    
    def generate_bullet_points(self, cv_data, pricing_data):
        """Generate bullet-point format explanation"""
        bullets = []
        
        bullets.append(f"Condition: {cv_data.get('overall_condition', 'good').capitalize()}")
        
        priority_issues = self.feature_extractor.prioritize_issues(cv_data, max_issues=3)
        if priority_issues:
            for issue in priority_issues:
                issue_text = self.template_manager.format_issue_description(issue)
                bullets.append(f"Note: {issue_text.capitalize()}")
        
        discount = pricing_data.get('discount_percentage', 0)
        used_price = pricing_data.get('calculated_used_price', 0)
        
        bullets.append(
            f"Price: {self.template_manager.format_price(used_price)} "
            f"({self.template_manager.format_percentage(discount)} discount)"
        )
        
        return bullets