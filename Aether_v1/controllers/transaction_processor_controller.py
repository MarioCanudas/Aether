import pandas as pd
from io import BytesIO
from typing import List, Dict, Any, Tuple, Literal
import logging
from streamlit import session_state
from services import (
    DataProcessingService, 
    FinancialAnalysisService,
    PlottingService, DataValidationService, DatabaseService
)
from .base_controller import BaseController
from utils import cache_by_transactions

logger = logging.getLogger(__name__)

class TransactionProcessorController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.financial_analysis_service = FinancialAnalysisService()
        self.plotting_service = PlottingService()
        self.data_validation_service = DataValidationService()
        
    def user_have_transactions(self) -> bool:
        user_id = self.user_session_service.current_user_id
        
        if user_id is None:
            logger.warning("No user is logged in")
            return False
        
        with self.quick_read_scope() as db:
            transactions = db.get_records(
                table_name='transactions',
                where_conditions={'user_id': user_id},
                value_format='tuple',
                limit=1
            )
            return len(transactions) > 0
        
    def user_have_monthly_results(self) -> bool:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_scope() as db:
            monthly_results = db.get_records(
                table_name='monthly_results',
                where_conditions={'user_id': user_id},
                value_format='tuple',
                limit=1
            )
            return len(monthly_results) > 0
        
    def process_uploaded_files(self, uploaded_files: list[BytesIO]) -> pd.DataFrame:
        all_transactions = []
        
        for uploaded_file in uploaded_files:
            try:
                df_transactions = self.data_processing_service.get_transactions_from_pdf(uploaded_file)
                all_transactions.append(df_transactions)
            except ValueError as e:
                logger.error(f"Error processing {uploaded_file.name}: {e}")
            except Exception as e:
                logger.error(f"An unexpected error processing {uploaded_file.name}: {e}")
                
        all_transactions_df = pd.concat(all_transactions, ignore_index=True)
        all_transactions_df['user_id'] = self.user_session_service.current_user_id
        
        return all_transactions_df
    
    def filter_transactions(
            self, 
            db_service: DatabaseService, 
            transactions: pd.DataFrame,
            value_format: Literal['dataframe', 'records'] = 'records'
        ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        transactions_cleaned = self.data_validation_service.delete_double_transactions(transactions)
        records = transactions_cleaned.to_dict(orient='records')
        
        filtered_records = []
        duplicate_records = []
        
        for record in records:
            if self.data_validation_service.check_if_transaction_exists_in_db(db_service, record):
                duplicate_records.append(record)
            else:
                filtered_records.append(record)
                
        if value_format == 'dataframe':
            filtered_records = pd.DataFrame(filtered_records)
            duplicate_records = pd.DataFrame(duplicate_records)
                
        return filtered_records, duplicate_records
    
    def filter_monthly_results(
            self,
            db_service: DatabaseService,
            monthly_results: pd.DataFrame,
            value_format: Literal['dataframe', 'records'] = 'records'
        ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        filtered_records = []
        duplicate_records = []
        
        for record in monthly_results:
            if self.data_validation_service.check_if_monthly_result_exists_in_db(db_service, record):
                duplicate_records.append(record)
            else:
                filtered_records.append(record)
                
        if value_format == 'dataframe':
            filtered_records = pd.DataFrame(filtered_records)
            duplicate_records = pd.DataFrame(duplicate_records)
                
        return filtered_records, duplicate_records
    
    def update_transactions(self, transactions: pd.DataFrame) -> None:
        with self.batch_scope() as db:
            filtered_records, duplicate_records = self.filter_transactions(db, transactions)
                    
            if duplicate_records:   
                logger.warning(f"{len(duplicate_records)} duplicate records found")
                
            if not filtered_records:
                logger.warning("No records to insert into the transactions table")
                return
            
            db.insert_multiple_records('transactions', filtered_records)
            logger.info(f"Inserted {len(filtered_records)} records into the transactions table")
            
    def update_monthly_results(self, transactions: pd.DataFrame) -> None:
        with self.batch_scope() as db:
            monthly_results = self.data_processing_service.calculate_savings_and_validate_balances(transactions, return_type='dataframe')
            monthly_results['year_month'] = monthly_results['year_month'].astype(str)
            monthly_results['user_id'] = self.user_session_service.current_user_id  
            monthly_results = monthly_results.to_dict(orient='records')
            
            filtered_records, duplicate_records = self.filter_monthly_results(db, monthly_results)
            
            if duplicate_records:
                logger.warning(f"{len(duplicate_records)} duplicate records found")
                
            if not filtered_records:
                logger.warning("No records to insert into the monthly_results table")
                return
                        
            db.insert_multiple_records('monthly_results', filtered_records)
            logger.info(f"Inserted {len(filtered_records)} records into the monthly_results table")
            
    def get_transactions(self) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_scope() as db:
            transactions = db.get_records(
                table_name='transactions',
                where_conditions={'user_id': user_id},
                value_format='dataframe'
            )
            return transactions
        
    def get_monthly_results(self) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_scope() as db:
            monthly_results = db.get_records(
                table_name='monthly_results',
                where_conditions={'user_id': user_id},
                value_format='dataframe'
            )
            return monthly_results
    
    def get_financial_analysis(self) -> dict:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_scope() as db:
            total_savings = self.financial_analysis_service.get_total_savings(db, user_id)
            avg_income_per_month = self.financial_analysis_service.get_avg_income_per_month(db, user_id)
            avg_withdrawal_per_month = self.financial_analysis_service.get_avg_withdrawal_per_month(db, user_id)

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