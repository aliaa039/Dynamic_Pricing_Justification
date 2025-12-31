import random
from src.utils.config import Config

class TemplateManager:
    """Manage text templates and phrase generation"""
    
    def __init__(self):
        self.templates = Config.load_templates()
    
    def get_condition_opening(self, condition):
        """Get opening statement based on overall condition"""
        condition_data = self.templates['condition_descriptors'].get(condition, {})
        return condition_data.get('opening', 'This item is in good condition.')
    
    def get_issue_phrase(self, issue_type, severity):
        """Get phrase for specific issue type and severity"""
        issue_phrases = self.templates['issue_phrases'].get(issue_type, {})
        return issue_phrases.get(severity, f"{severity} {issue_type}")
    
    def get_location_phrase(self, location):
        """Get phrase for issue location"""
        return self.templates['location_phrases'].get(location, f"on the {location}")
    
    def get_discount_explanation(self, discount_percentage):
        """Get explanation phrase based on discount level"""
        for level, data in self.templates['discount_explanations'].items():
            min_discount, max_discount = data['range']
            if min_discount <= discount_percentage <= max_discount:
                return data['phrase']
        
        return "The condition is reflected in the pricing"
    
    def get_transition_phrase(self):
        """Get random transition phrase for better flow"""
        return random.choice(self.templates['transition_phrases'])
    
    def get_positive_closing(self):
        """Get positive closing statement"""
        return random.choice(self.templates['positive_closings'])
    
    def format_issue_description(self, issue):
        """Format a single issue into natural language"""
        issue_phrase = self.get_issue_phrase(issue['type'], issue['severity'])
        location_phrase = self.get_location_phrase(issue['location'])
        
        return f"{issue_phrase} {location_phrase}"
    
    def format_multiple_issues(self, issues):
        """Format multiple issues into a coherent sentence"""
        if not issues:
            return ""
        
        if len(issues) == 1:
            return self.format_issue_description(issues[0])
        
        formatted_issues = [self.format_issue_description(issue) for issue in issues]
        
        if len(formatted_issues) == 2:
            return f"{formatted_issues[0]} and {formatted_issues[1]}"
        else:
            last_issue = formatted_issues[-1]
            other_issues = ", ".join(formatted_issues[:-1])
            return f"{other_issues}, and {last_issue}"
    
    def format_price(self, price):
        """Format price with currency and proper formatting"""
        return f"${price:,.2f}"
    
    def format_percentage(self, percentage):
        """Format percentage"""
        return f"{percentage}%"