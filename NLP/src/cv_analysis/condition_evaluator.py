"""
Condition Evaluator
Converts Gemini CV analysis to standardized condition format
"""
from typing import Dict, List

class ConditionEvaluator:
    """Evaluates device condition from CV analysis"""
    
    SEVERITY_MAP = {
        'low': 'minor',
        'medium': 'moderate',
        'high': 'severe'
    }
    
    def evaluate_from_gemini(
        self, 
        gemini_analysis: Dict, 
        usage_years: float
    ) -> Dict:
        """
        Convert Gemini format to internal CV format
        
        Gemini format (from Streamlit app):
        {
            "Front screen": {
                "issues": [
                    {
                        "type": "scratches",
                        "severity": "low",
                        "location": "top-left corner",
                        "description": "visible surface scratches"
                    }
                ],
                "overall_condition": "good"
            }
        }
        
        Returns (internal format):
        {
            "condition_score": 8.0,
            "overall_condition": "good",
            "detected_issues": [...],
            "metadata": {...}
        }
        """
        all_issues = []
        condition_counts = self._count_conditions(gemini_analysis)
        
        # Extract all issues from all views
        for view, analysis in gemini_analysis.items():
            for issue in analysis.get('issues', []):
                all_issues.append(self._format_issue(issue, view))
        
        # Calculate overall condition
        overall_condition = self._determine_overall_condition(
            condition_counts, len(gemini_analysis)
        )
        
        # Calculate numeric score
        condition_score = self._calculate_condition_score(
            overall_condition, len(all_issues), usage_years
        )
        
        return {
            'condition_score': round(condition_score, 1),
            'overall_condition': overall_condition,
            'detected_issues': all_issues,
            'metadata': {
                'total_views_analyzed': len(gemini_analysis),
                'usage_years': usage_years,
                **condition_counts
            }
        }
    
    def _count_conditions(self, analysis: Dict) -> Dict:
        """Count condition types across all views"""
        counts = {'pristine': 0, 'good': 0, 'fair': 0, 'poor': 0}
        
        for view_data in analysis.values():
            condition = view_data.get('overall_condition', '').lower()
            if condition in counts:
                counts[condition] += 1
        
        return counts
    
    def _format_issue(self, issue: Dict, view: str) -> Dict:
        """Format single issue to standard format"""
        return {
            'type': issue.get('type', 'unknown'),
            'location': f"{view} - {issue.get('location', 'unknown')}",
            'severity': self.SEVERITY_MAP.get(
                issue.get('severity', 'low'), 'minor'
            ),
            'confidence': 0.85,
            'description': issue.get('description', '')
        }
    
    def _determine_overall_condition(
        self, 
        condition_counts: Dict, 
        total_views: int
    ) -> str:
        """Determine overall condition from view counts"""
        if condition_counts['pristine'] >= total_views * 0.6:
            return 'excellent'
        elif condition_counts['good'] >= total_views * 0.5:
            return 'good'
        elif condition_counts['fair'] >= total_views * 0.4:
            return 'fair'
        else:
            return 'poor'
    
    def _calculate_condition_score(
        self,
        overall_condition: str,
        num_issues: int,
        usage_years: float
    ) -> float:
        """Calculate numeric condition score (1-10)"""
        base_scores = {
            'excellent': 9.5,
            'good': 8.0,
            'fair': 6.0,
            'poor': 4.0
        }
        
        base_score = base_scores.get(overall_condition, 5.0)
        issue_penalty = num_issues * 0.3
        usage_penalty = min(usage_years * 0.2, 2.0)
        
        return max(1.0, base_score - issue_penalty - usage_penalty)