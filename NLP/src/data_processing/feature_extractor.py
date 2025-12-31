from src.utils.config import Config

class FeatureExtractor:
    """Extract and process features from CV output"""
    
    def __init__(self):
        self.config = Config()
    
    def extract_condition_features(self, cv_data):
        """Extract meaningful features from CV output"""
        return {
            'overall_condition': cv_data.get('overall_condition', 'good'),
            'condition_score': cv_data.get('condition_score', 7.0),
            'issue_count': len(cv_data.get('detected_issues', [])),
            'severity_distribution': self._analyze_severity_distribution(cv_data),
            'most_critical_issue': self._get_most_critical_issue(cv_data),
            'location_distribution': self._analyze_locations(cv_data)
        }
    
    def _analyze_severity_distribution(self, cv_data):
        """Count issues by severity"""
        distribution = {'minor': 0, 'moderate': 0, 'severe': 0}
        
        for issue in cv_data.get('detected_issues', []):
            severity = issue.get('severity', 'minor')
            if severity in distribution:
                distribution[severity] += 1
        
        return distribution
    
    def _get_most_critical_issue(self, cv_data):
        """Find the most critical issue based on priority and severity"""
        issues = cv_data.get('detected_issues', [])
        
        if not issues:
            return None
        
        scored_issues = []
        for issue in issues:
            priority = Config.get_issue_priority(issue.get('type', ''))
            severity_weight = Config.get_severity_weight(issue.get('severity', 'minor'))
            confidence = issue.get('confidence', 0.5)
            
            score = priority * severity_weight * confidence
            scored_issues.append((score, issue))
        
        scored_issues.sort(reverse=True, key=lambda x: x[0])
        return scored_issues[0][1] if scored_issues else None
    
    def _analyze_locations(self, cv_data):
        """Analyze distribution of issues across locations"""
        locations = {}
        
        for issue in cv_data.get('detected_issues', []):
            location = issue.get('location', 'unknown')
            if location not in locations:
                locations[location] = []
            locations[location].append(issue)
        
        return locations
    
    def prioritize_issues(self, cv_data, max_issues=3):
        """Select top priority issues to mention in description"""
        issues = cv_data.get('detected_issues', [])
        
        if not issues:
            return []
        
        scored_issues = []
        for issue in issues:
            priority = Config.get_issue_priority(issue.get('type', ''))
            severity_weight = Config.get_severity_weight(issue.get('severity', 'minor'))
            confidence = issue.get('confidence', 0.5)
            
            score = priority * severity_weight * confidence
            scored_issues.append((score, issue))
        
        scored_issues.sort(reverse=True, key=lambda x: x[0])
        
        return [issue for _, issue in scored_issues[:max_issues]]
    
    def calculate_overall_impact_score(self, cv_data):
        """Calculate overall impact score from all issues"""
        issues = cv_data.get('detected_issues', [])
        
        if not issues:
            return 0.0
        
        total_impact = 0
        for issue in issues:
            priority = Config.get_issue_priority(issue.get('type', ''))
            severity_weight = Config.get_severity_weight(issue.get('severity', 'minor'))
            confidence = issue.get('confidence', 0.5)
            
            total_impact += priority * severity_weight * confidence
        
        max_possible = len(issues) * 5 * 3 * 1.0
        normalized_score = (total_impact / max_possible) * 10 if max_possible > 0 else 0
        
        return round(normalized_score, 2)