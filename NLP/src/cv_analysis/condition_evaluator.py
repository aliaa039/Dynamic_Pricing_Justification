"""
Condition Evaluator - Extracts structured condition data from Gemini CV analysis
"""

from typing import Dict, List

class ConditionEvaluator:
    """
    Evaluates device condition from Gemini computer vision analysis results.
    Converts qualitative assessments to quantitative scores.
    """
    
    # Condition scoring mapping
    CONDITION_SCORES = {
        'excellent': 9.5,
        'very good': 8.5,
        'good': 7.0,
        'fair': 5.0,
        'poor': 3.0,
        'damaged': 2.0,
        'broken': 1.0
    }
    
    # Severity weights for discount calculation
    SEVERITY_WEIGHTS = {
        'minor': 0.02,      # 2% impact
        'moderate': 0.05,   # 5% impact
        'severe': 0.10,     # 10% impact
        'critical': 0.15    # 15% impact
    }
    
    def evaluate_from_gemini(
        self, 
        gemini_analysis: Dict, 
        usage_years: float = 1.0
    ) -> Dict:
        """
        Convert Gemini analysis results to structured condition metrics.
        
        Input format (from st.session_state.analysis_results):
        {
            "Front": {
                "overall_condition": "good",
                "damage_details": {
                    "scratches": [{"severity": "minor", "location": "top-left"}],
                    "cracks": []
                }
            },
            "Back": {
                "overall_condition": "damaged",
                "damage_details": {...}
            }
        }
        
        Output:
        {
            "overall_condition": "good",
            "condition_score": 7.5,
            "detected_issues": [
                {
                    "type": "scratch",
                    "severity": "minor",
                    "location": "front top-left",
                    "impact": 0.02
                }
            ],
            "severity_distribution": {
                "minor": 2,
                "moderate": 1,
                "severe": 0
            },
            "total_discount_impact": 0.09,
            "usage_years": 1.0
        }
        """
        
        if not gemini_analysis:
            return self._get_default_condition(usage_years)
        
        # Collect all conditions and issues from all views
        all_conditions = []
        all_issues = []
        
        for view_name, analysis in gemini_analysis.items():
            condition = analysis.get('overall_condition', 'good').lower()
            all_conditions.append(condition)
            
            # Extract damage details
            damage_details = analysis.get('damage_details', {})
            
            for damage_type, items in damage_details.items():
                if items and isinstance(items, list):
                    for item in items:
                        issue = self._create_issue_entry(
                            damage_type=damage_type,
                            view=view_name,
                            details=item
                        )
                        all_issues.append(issue)
        
        # Determine overall condition (worst case scenario)
        overall_condition = self._determine_overall_condition(all_conditions)
        
        # Calculate condition score
        base_score = self.CONDITION_SCORES.get(overall_condition, 7.0)
        condition_score = self._adjust_score_for_issues(base_score, all_issues)
        
        # Calculate severity distribution
        severity_dist = self._calculate_severity_distribution(all_issues)
        
        # Calculate total discount impact
        total_impact = self._calculate_discount_impact(all_issues)
        
        return {
            'overall_condition': overall_condition,
            'condition_score': round(condition_score, 2),
            'detected_issues': all_issues,
            'severity_distribution': severity_dist,
            'total_discount_impact': round(total_impact, 3),
            'usage_years': usage_years,
            'views_analyzed': list(gemini_analysis.keys()),
            'issues_count': len(all_issues)
        }
    
    def _create_issue_entry(
        self, 
        damage_type: str, 
        view: str, 
        details: Dict
    ) -> Dict:
        """
        Create a standardized issue entry.
        
        Args:
            damage_type: "scratches", "cracks", "dents", etc.
            view: "Front", "Back", "Side", etc.
            details: {"severity": "minor", "location": "top-left"}
        
        Returns:
            {
                "type": "scratch",
                "severity": "minor",
                "location": "back top-left",
                "impact": 0.02
            }
        """
        # Normalize damage type (remove plural)
        normalized_type = damage_type.rstrip('s').lower()
        
        # Get severity
        severity = details.get('severity', 'minor').lower()
        
        # Combine view and location
        detail_location = details.get('location', '')
        full_location = f"{view.lower()} {detail_location}".strip()
        
        # Get impact weight
        impact = self.SEVERITY_WEIGHTS.get(severity, 0.02)
        
        return {
            'type': normalized_type,
            'severity': severity,
            'location': full_location,
            'impact': impact,
            'view': view
        }
    
    def _determine_overall_condition(self, conditions: List[str]) -> str:
        """
        Determine overall condition from multiple view conditions.
        Uses worst-case scenario (most damaged condition wins).
        """
        if not conditions:
            return 'good'
        
        # Priority order (worst to best)
        priority = [
            'broken', 'damaged', 'poor', 'fair', 
            'good', 'very good', 'excellent'
        ]
        
        # Find worst condition
        for level in priority:
            if level in conditions:
                return level
        
        return 'good'
    
    def _adjust_score_for_issues(
        self, 
        base_score: float, 
        issues: List[Dict]
    ) -> float:
        """
        Adjust condition score based on number and severity of issues.
        """
        if not issues:
            return base_score
        
        # Deduct points based on issues
        total_deduction = 0
        
        for issue in issues:
            severity = issue.get('severity', 'minor')
            
            # Deduction per issue type
            deductions = {
                'critical': 1.5,
                'severe': 1.0,
                'moderate': 0.5,
                'minor': 0.2
            }
            
            total_deduction += deductions.get(severity, 0.2)
        
        # Apply deduction with minimum score of 1.0
        adjusted_score = max(1.0, base_score - total_deduction)
        
        return adjusted_score
    
    def _calculate_severity_distribution(self, issues: List[Dict]) -> Dict:
        """Calculate how many issues of each severity level exist."""
        distribution = {
            'minor': 0,
            'moderate': 0,
            'severe': 0,
            'critical': 0
        }
        
        for issue in issues:
            severity = issue.get('severity', 'minor')
            if severity in distribution:
                distribution[severity] += 1
        
        return distribution
    
    def _calculate_discount_impact(self, issues: List[Dict]) -> float:
        """
        Calculate total discount impact as a percentage.
        This will be used by PriceCalculator for additional discounting.
        
        Returns:
            Float between 0.0 and 1.0 (e.g., 0.15 = 15% additional discount)
        """
        if not issues:
            return 0.0
        
        total_impact = sum(issue.get('impact', 0.02) for issue in issues)
        
        # Cap maximum impact at 30% (0.30)
        return min(0.30, total_impact)
    
    def _get_default_condition(self, usage_years: float) -> Dict:
        """Return default condition when no CV analysis is available."""
        return {
            'overall_condition': 'good',
            'condition_score': 7.0,
            'detected_issues': [],
            'severity_distribution': {
                'minor': 0,
                'moderate': 0,
                'severe': 0,
                'critical': 0
            },
            'total_discount_impact': 0.0,
            'usage_years': usage_years,
            'views_analyzed': [],
            'issues_count': 0
        }
    
    def get_condition_summary(self, evaluation: Dict) -> str:
        """
        Generate human-readable condition summary.
        Useful for displaying in UI.
        """
        condition = evaluation.get('overall_condition', 'good')
        score = evaluation.get('condition_score', 7.0)
        issues = evaluation.get('detected_issues', [])
        
        if not issues:
            return f"Device is in {condition} condition (score: {score}/10) with no significant damage detected."
        
        issue_summary = self._summarize_issues(issues)
        
        return (
            f"Device is in {condition} condition (score: {score}/10). "
            f"Detected issues: {issue_summary}"
        )
    
    def _summarize_issues(self, issues: List[Dict]) -> str:
        """Create brief text summary of issues."""
        if not issues:
            return "none"
        
        # Group by severity
        by_severity = {}
        for issue in issues:
            sev = issue['severity']
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(f"{issue['type']} on {issue['location']}")
        
        # Format output
        parts = []
        for severity in ['critical', 'severe', 'moderate', 'minor']:
            if severity in by_severity:
                count = len(by_severity[severity])
                parts.append(f"{count} {severity} issue(s)")
        
        return ", ".join(parts)