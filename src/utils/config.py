import json
import os

class Config:
    """Configuration manager for the NLP module"""
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    CONFIG_DIR = os.path.join(BASE_DIR, 'config')
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    
    @staticmethod
    def load_templates():
        """Load text templates from config file"""
        templates_path = os.path.join(Config.CONFIG_DIR, 'templates.json')
        with open(templates_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def load_mock_data():
        """Load mock CV output for testing"""
        mock_path = os.path.join(Config.DATA_DIR, 'mock_cv_output.json')
        with open(mock_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def get_severity_weight(severity):
        """Get numerical weight for severity levels"""
        weights = {
            'minor': 1,
            'moderate': 2,
            'severe': 3
        }
        return weights.get(severity, 1)
    
    @staticmethod
    def get_issue_priority(issue_type):
        """Define priority for different issue types"""
        priorities = {
            'crack': 5,
            'dent': 4,
            'scratch': 3,
            'discoloration': 2,
            'wear': 1
        }
        return priorities.get(issue_type, 0)