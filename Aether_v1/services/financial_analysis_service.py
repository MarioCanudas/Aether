from decimal import Decimal
from datetime import date
from models.amounts import TransactionType
from models.financial import FinancialStatus, FinancialAmountsSums
from models.goals import GoalInfo, GoalProgressScore

class FinancialAnalysisService:   
    @staticmethod
    def get_financial_status_label(avg_financial_sums: FinancialAmountsSums) -> FinancialStatus:
        if avg_financial_sums.savings is None:
            return FinancialStatus.POOR
        
        if avg_financial_sums.savings >= Decimal(0.10) * avg_financial_sums.income:
            return FinancialStatus.EXCELLENT
        elif 0 <= avg_financial_sums.savings < Decimal(0.10) * avg_financial_sums.income:
            return FinancialStatus.GOOD
        elif Decimal(-0.10) * avg_financial_sums.income <= avg_financial_sums.savings < 0:
            return FinancialStatus.REGULAR
        else:
            return FinancialStatus.POOR
    
    @staticmethod
    def get_financial_tips(label: FinancialStatus) -> list[str]:
        """
        Returns financial tips based on the given financial health label.

        :param label: The financial health label (e.g., "Excellent!", "Decent", "Caution", "Alert!")
        :return: A list of 3 tips specific to the financial health situation.
        """ 
        if label == FinancialStatus.EXCELLENT:
            return [
                "Consider investing more to grow your wealth.",
                "Maintain your current savings habits to ensure long-term financial stability.",
                "Explore tax-saving opportunities for greater efficiency."
            ]
        elif label == FinancialStatus.GOOD:
            return [
                "Focus on increasing your savings by cutting unnecessary expenses.",
                "Review your investment portfolio and make adjustments where needed.",
                "Set clear financial goals to improve your savings rate."
            ]
        elif label == FinancialStatus.REGULAR:
            return [
                "Reduce discretionary spending to improve your savings rate.",
                "Create a detailed budget and stick to it for better financial management.",
                "Consider automating your savings to avoid overspending."
            ]
        elif label == FinancialStatus.POOR:
            return [
                "Take immediate action to reduce your debt and manage your expenses.",
                "Seek professional financial advice to get back on track.",
                "Focus on building an emergency fund to improve your financial health."
            ]
        else:
            return ["No specific tips available for this financial health situation."]

    @staticmethod
    def get_goal_progress_score(goal_info: GoalInfo) -> GoalProgressScore:
        total_amount = goal_info.amount + goal_info.added_amount
        total_days = (goal_info.end_date - goal_info.start_date).days
        days_elapsed = (date.today() - goal_info.start_date).days
        current_amount = goal_info.current_amount
        
        eps = 1e-9
        p = 2
        
        if total_amount <= 0 or total_days <= 0:
            raise ValueError("Total amount and total days must be greater than 0")
        amount_progress = abs(current_amount) / total_amount
        
        days_progress = max(days_elapsed / total_days, 1.0 / total_days)
        if goal_info.type.transaction_type == TransactionType.INCOME:
            r = amount_progress / max(days_progress, eps)
        elif goal_info.type.transaction_type == TransactionType.EXPENSE:
            rem = max(0.0, 1.0 - amount_progress)
            re  = max(0.0, 1.0 - days_progress)
            re = max(re, 1.0 / total_amount)  
            r = rem / max(re, eps)
        else:
            raise ValueError("kind must be 'positive' or 'budget'")
        
        score = (r**p) / (1.0 + r**p)
        
        return GoalProgressScore(score= float(max(0.0, min(1.0, score))))
