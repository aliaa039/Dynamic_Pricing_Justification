class DiscountExplainer:
    """Explain discount breakdown in detail"""
    
    def explain_discount_breakdown(self, price_factors):
        """Generate detailed breakdown of discount factors"""
        base_dep = price_factors.get('base_depreciation', 0)
        condition_adj = price_factors.get('condition_adjustment', 0)
        issue_penalty = price_factors.get('issue_penalty', 0)
        
        breakdown = []
        
        if base_dep > 0:
            breakdown.append(f"{base_dep}% from overall condition score")
        
        if condition_adj > 0:
            breakdown.append(f"{condition_adj}% from condition category")
        
        if issue_penalty > 0:
            breakdown.append(f"{round(issue_penalty, 1)}% from detected issues")
        
        return breakdown
    
    def generate_breakdown_text(self, price_factors, total_discount):
        """Generate human-readable breakdown text"""
        breakdown_items = self.explain_discount_breakdown(price_factors)
        
        if not breakdown_items:
            return "No discount factors applied."
        
        text = f"The {total_discount}% discount consists of: "
        text += ", ".join(breakdown_items)
        text += "."
        
        return text
    
    def compare_to_market(self, used_price, market_average=None):
        """Compare price to market average"""
        if market_average is None:
            return None
        
        difference = ((used_price - market_average) / market_average) * 100
        
        if difference < -10:
            return f"This price is {abs(round(difference))}% below market average"
        elif difference > 10:
            return f"This price is {round(difference)}% above market average"
        else:
            return "This price is competitive with market average"
    
    def get_value_proposition(self, discount_percentage):
        """Get value proposition statement based on discount level"""
        if discount_percentage < 15:
            return "Premium condition with minimal wear"
        elif discount_percentage < 30:
            return "Good value for a well-maintained item"
        elif discount_percentage < 50:
            return "Significant savings on a functional item"
        else:
            return "Maximum savings for budget-conscious buyers"