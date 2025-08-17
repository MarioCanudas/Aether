from decimal import Decimal
from typing import List
from models.financial import SummaryMetrics, FinancialStatus

class FinancialAnalysisService:   
    @staticmethod
    def get_financial_status_label(summary_metrics: SummaryMetrics) -> FinancialStatus:
        if summary_metrics.total_savings >= Decimal(0.10) * summary_metrics.avg_income_per_month:
            return FinancialStatus.EXCELLENT
        elif 0 <= summary_metrics.total_savings < Decimal(0.10) * summary_metrics.avg_income_per_month:
            return FinancialStatus.GOOD
        elif Decimal(-0.10) * summary_metrics.avg_income_per_month <= summary_metrics.total_savings < 0:
            return FinancialStatus.REGULAR
        else:
            return FinancialStatus.POOR
    
    @staticmethod
    def get_financial_tips(label: FinancialStatus) -> List[str]:
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
