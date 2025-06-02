from pandas import DataFrame
from io import BytesIO
from streamlit import session_state
from services import DataProcessingService, FinancialAnalysisService, PlottingService

class TransactionProcessorController:   
    def initialize_session_state(self) -> None:
        # Initialize session state for storing transactions
        if 'all_transactions' not in session_state:
            session_state.all_transactions = []
        if 'all_processed_data' not in session_state:
            session_state.all_processed_data = DataFrame()
        if 'all_monthly_results' not in session_state:
            session_state.all_monthly_results = DataFrame()
     
    def process_uploaded_file(self, uploaded_file: BytesIO) -> DataFrame:
        data_processing_service = DataProcessingService()

        return data_processing_service.process_uploaded_file(uploaded_file, session_state.all_transactions)
    
    def append_transactions(self, transactions: DataFrame) -> None:
        session_state.all_transactions.append(transactions)
                
    def get_combined_df(self) -> DataFrame:
        data_processing_service = DataProcessingService()
        
        return data_processing_service.combine_transactions(session_state.all_transactions)
        
    def get_cleaned_df(self) -> DataFrame:
        data_processing_service = DataProcessingService()
        
        combined_df = self.get_combined_df()
        return data_processing_service.delete_double_transactions(combined_df)
    
    def get_monthly_results(self) -> DataFrame:
        data_processing_service = DataProcessingService()
        
        cleaned_df = self.get_cleaned_df()
        return data_processing_service.calculate_savings_and_validate_balances(cleaned_df).sort_values(by='Month', ascending=True)
    
    def update_all_processed_data(self) -> None:
        session_state.all_processed_data = self.get_combined_df()
        
    def update_all_monthly_results(self) -> None:
        session_state.all_monthly_results = self.get_monthly_results()
        
    def clear_all_transactions(self) -> None:
        session_state.all_transactions = []
        session_state.monthly_results = DataFrame()
        
    def get_financial_analysis(self) -> dict:
        financial_analysis_service = FinancialAnalysisService(session_state.all_monthly_results)
        plotting_service = PlottingService()

        total_savings = financial_analysis_service.get_total_savings()
        avg_income_per_month = financial_analysis_service.get_avg_income_per_month()
        avg_withdrawal_per_month = financial_analysis_service.get_avg_withdrawal_per_month()

        donut_score_chart, label = plotting_service.get_plot_savings_donut_chart(total_savings, avg_income_per_month)
        
        tips = financial_analysis_service.get_financial_tips(label)

        return {
            'total_savings': total_savings,
            'avg_income_per_month': avg_income_per_month,
            'avg_withdrawal_per_month': avg_withdrawal_per_month,
            'donut_score_chart': donut_score_chart,
            'label': label,
            'tips': tips
        }
