class InputValidator:
    """Validate input data from CV team and pricing module"""
    
    REQUIRED_CV_FIELDS = ['item_id', 'condition_score', 'detected_issues', 'overall_condition']
    REQUIRED_ISSUE_FIELDS = ['type', 'location', 'severity', 'confidence']
    VALID_CONDITIONS = ['excellent', 'good', 'fair', 'poor']
    VALID_SEVERITIES = ['minor', 'moderate', 'severe']
    
    @staticmethod
    def validate_cv_output(cv_data):
        """Validate CV team output structure"""
        errors = []
        
        for field in InputValidator.REQUIRED_CV_FIELDS:
            if field not in cv_data:
                errors.append(f"Missing required field: {field}")
        
        if 'condition_score' in cv_data:
            score = cv_data['condition_score']
            if not isinstance(score, (int, float)) or not (0 <= score <= 10):
                errors.append("condition_score must be between 0 and 10")
        
        if 'overall_condition' in cv_data:
            if cv_data['overall_condition'] not in InputValidator.VALID_CONDITIONS:
                errors.append(f"Invalid overall_condition. Must be one of: {InputValidator.VALID_CONDITIONS}")
        
        if 'detected_issues' in cv_data:
            if not isinstance(cv_data['detected_issues'], list):
                errors.append("detected_issues must be a list")
            else:
                for idx, issue in enumerate(cv_data['detected_issues']):
                    issue_errors = InputValidator._validate_issue(issue, idx)
                    errors.extend(issue_errors)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def _validate_issue(issue, index):
        """Validate individual issue structure"""
        errors = []
        
        for field in InputValidator.REQUIRED_ISSUE_FIELDS:
            if field not in issue:
                errors.append(f"Issue {index}: Missing field '{field}'")
        
        if 'severity' in issue and issue['severity'] not in InputValidator.VALID_SEVERITIES:
            errors.append(f"Issue {index}: Invalid severity. Must be one of: {InputValidator.VALID_SEVERITIES}")
        
        if 'confidence' in issue:
            conf = issue['confidence']
            if not isinstance(conf, (int, float)) or not (0 <= conf <= 1):
                errors.append(f"Issue {index}: confidence must be between 0 and 1")
        
        return errors
    
    @staticmethod
    def validate_pricing_data(pricing_data):
        """Validate pricing module data"""
        errors = []
        
        required_fields = ['reference_new_price', 'calculated_used_price', 'discount_percentage']
        
        for field in required_fields:
            if field not in pricing_data:
                errors.append(f"Missing required field: {field}")
        
        if 'reference_new_price' in pricing_data and pricing_data['reference_new_price'] <= 0:
            errors.append("reference_new_price must be positive")
        
        if 'calculated_used_price' in pricing_data and pricing_data['calculated_used_price'] < 0:
            errors.append("calculated_used_price cannot be negative")
        
        if 'discount_percentage' in pricing_data:
            discount = pricing_data['discount_percentage']
            if not (0 <= discount <= 100):
                errors.append("discount_percentage must be between 0 and 100")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }