import pandas as pd
from .database_service import DatabaseService

class FinancialAnalysisService: 
    @staticmethod
    def get_total_savings(db_service: DatabaseService, user_id: int) -> float:
        query = """
        SELECT SUM(savings) FROM monthly_results
        WHERE user_id = :user_id
        """
        return db_service.custom_query(query, {'user_id': user_id}, value_format='scalar')
    
    @staticmethod
    def get_avg_income_per_month(db_service: DatabaseService, user_id: int) -> float:
        query = """
        SELECT AVG(total_income) FROM monthly_results
        WHERE user_id = :user_id
        """
        return db_service.custom_query(query, {'user_id': user_id}, value_format='scalar')
    
    @staticmethod
    def get_avg_withdrawal_per_month(db_service: DatabaseService, user_id: int) -> float:
        query = """
        SELECT AVG(total_withdrawal) FROM monthly_results
        WHERE user_id = :user_id
        """
        return db_service.custom_query(query, {'user_id': user_id}, value_format='scalar')
        
    @staticmethod
    def get_financial_tips(label: str) -> list[str]:
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
