import pandas as pd

class FinancialAnalysisService:
    def __init__(self, all_monthly_results: pd.DataFrame):
        self.all_monthly_results = all_monthly_results
        
    def get_total_savings(self) -> float:
        return self.all_monthly_results['savings'].sum()
    
    def get_avg_income_per_month(self) -> float:
        return self.all_monthly_results['total_income'].mean()
    
    def get_avg_withdrawal_per_month(self) -> float:
        return self.all_monthly_results['total_withdrawal'].mean()
        
    def get_financial_tips(self, label):
        """
        Returns financial tips based on the given financial health label.

        :param label: The financial health label (e.g., "Excellent!", "Decent", "Caution", "Alert!")
        :return: A list of 3 tips specific to the financial health situation.
        """
        # Ensure that the label is lowercased and stripped of any extra spaces
        label = label.strip().lower()

        if label == "excellent!":
            return [
                "Consider investing more to grow your wealth.",
                "Maintain your current savings habits to ensure long-term financial stability.",
                "Explore tax-saving opportunities for greater efficiency."
            ]
        elif label == "good":
            return [
                "Focus on increasing your savings by cutting unnecessary expenses.",
                "Review your investment portfolio and make adjustments where needed.",
                "Set clear financial goals to improve your savings rate."
            ]
        elif label == "regular":
            return [
                "Reduce discretionary spending to improve your savings rate.",
                "Create a detailed budget and stick to it for better financial management.",
                "Consider automating your savings to avoid overspending."
            ]
        elif label == "poor":
            return [
                "Take immediate action to reduce your debt and manage your expenses.",
                "Seek professional financial advice to get back on track.",
                "Focus on building an emergency fund to improve your financial health."
            ]
        else:
            return ["No specific tips available for this financial health situation."]
