from pandas import DataFrame
from io import BytesIO
from streamlit import session_state
from services import DataProcessingService, FinancialAnalysisService, PlottingService
from .base_controller import BaseController

class TransactionProcessorController(BaseController):   
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        if 'all_monthly_results' in session_state:
            self.financial_analysis_service = FinancialAnalysisService(session_state.all_monthly_results)
        else:
            self.financial_analysis_service = FinancialAnalysisService(DataFrame())
        self.plotting_service = PlottingService()
        
    def initialize_session_state(self) -> None:
        # Initialize session state for storing transactions
        if 'all_transactions' not in session_state:
            session_state.all_transactions = []
        if 'all_processed_data' not in session_state:
            session_state.all_processed_data = DataFrame()
        if 'all_monthly_results' not in session_state:
            session_state.all_monthly_results = DataFrame()
     
    def process_uploaded_file(self, uploaded_file: BytesIO) -> DataFrame:
        return self.data_processing_service.process_uploaded_file(uploaded_file, session_state.all_transactions)
    
    def append_transactions(self, transactions: DataFrame) -> None:
        session_state.all_transactions.append(transactions)
                
    def get_combined_df(self) -> DataFrame:
        return self.data_processing_service.combine_transactions(session_state.all_transactions)
        
    def get_cleaned_df(self) -> DataFrame:
        combined_df = self.get_combined_df()
        return self.data_processing_service.delete_double_transactions(combined_df)
    
    def get_monthly_results(self) -> DataFrame:
        cleaned_df = self.get_cleaned_df()
        return self.data_processing_service.calculate_savings_and_validate_balances(cleaned_df).sort_values(by='Month', ascending=True)
    
    def update_all_processed_data(self) -> None:
        session_state.all_processed_data = self.get_combined_df()
        
    def update_all_monthly_results(self) -> None:
        session_state.all_monthly_results = self.get_monthly_results()
        
    def clear_all_transactions(self) -> None:
        session_state.all_transactions = []
        session_state.all_processed_data = DataFrame()
        session_state.all_monthly_results = DataFrame()
        
    def get_financial_analysis(self) -> dict:
        # Update the financial analysis service with the latest monthly results
        self.financial_analysis_service = FinancialAnalysisService(session_state.all_monthly_results)
        
        total_savings = self.financial_analysis_service.get_total_savings()
        avg_income_per_month = self.financial_analysis_service.get_avg_income_per_month()
        avg_withdrawal_per_month = self.financial_analysis_service.get_avg_withdrawal_per_month()

        donut_score_chart, label = self.plotting_service.get_plot_savings_donut_chart(total_savings, avg_income_per_month)
        
        tips = self.financial_analysis_service.get_financial_tips(label)

        return {
            'total_savings': total_savings,
            'avg_income_per_month': avg_income_per_month,
            'avg_withdrawal_per_month': avg_withdrawal_per_month,
            'donut_score_chart': donut_score_chart,
            'label': label,
            'tips': tips
        }
