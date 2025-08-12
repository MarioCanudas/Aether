import pandas as pd
from io import BytesIO
from typing import List, Tuple, Dict, Any
import logging
from services import (
    StatementDataExtractionService,
    DataProcessingService, 
    FinancialAnalysisService,
    PlottingService, 
    DataValidationService,
    MonthlyResultDBService,
    TransactionsDBService
)
from models.tables import AllTransactionsTable, MonthlyResultsTable
from models.records import TransactionRecord, MonthlyResultRecord
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class TransactionProcessorController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.financial_analysis_service = FinancialAnalysisService()
        self.plotting_service = PlottingService()
        self.data_validation_service = DataValidationService()
        
    def process_uploaded_files(self, uploaded_files: list[BytesIO]) -> AllTransactionsTable:
        all_transactions = []
        
        for uploaded_file in uploaded_files:
            try:
                # Set the transaction extraction service per file
                statement_data_extraction_service = StatementDataExtractionService(uploaded_file)
                transactions_table = statement_data_extraction_service.get_transactions()
                metadata = statement_data_extraction_service.metadata_extractor.get_metadata()
                
                validated_transactions = self.data_validation_service.validate_transactions(transactions_table, metadata)
                
                all_transactions.append(validated_transactions.df)
            except ValueError as e:
                raise ValueError(f"Error processing {uploaded_file.name}: {e}")
            except Exception as e:
                raise ValueError(f"An unexpected error processing {uploaded_file.name}: {e}")
                
        all_transactions_df = pd.concat(all_transactions, ignore_index=True)
        all_transactions_df['user_id'] = self.user_session_service.current_user_id
        all_transactions_df['category_id'] = None
         
        return AllTransactionsTable(df=all_transactions_df)
    
    def filter_transactions(self, all_transactions: AllTransactionsTable) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        user_id = self.user_id
        
        transactions_cleaned = self.data_validation_service.delete_double_transactions(all_transactions)
        records = transactions_cleaned.records
        
        # Batch processing optimization
        if records:
            # Get existing transactions in a single query
            existing_keys = self.data_validation_service.get_existing_transaction_keys(records, user_id)
            
            filtered_records = []
            duplicate_records = []
            
            for record in records:
                # Create unique key for comparison
                key = (
                    record['date'].strftime('%Y-%m-%d') if hasattr(record['date'], 'strftime') else record['date'],
                    record['amount'],
                    record['description'],
                    record['bank'],
                    record['statement_type']
                )
                
                if key in existing_keys:
                    duplicate_records.append(record)
                else:
                    filtered_records.append(record)
        else:
            filtered_records = []
            duplicate_records = []
                
        return filtered_records, duplicate_records
    
    def filter_monthly_results(self, monthly_results: MonthlyResultsTable) -> Tuple[List[MonthlyResultRecord], List[MonthlyResultRecord]]:
        user_id = self.user_id
        records = monthly_results.records
            
        # Batch processing optimization
        if records:
            # Get existing monthly results in a single query
            existing_keys = self.data_validation_service.get_existing_monthly_result_keys(records, user_id)
            
            filtered_records = []
            duplicate_records = []
            
            for record in records:
                key = record['year_month']
                if key in existing_keys:
                    duplicate_records.append(record)
                else:
                    filtered_records.append(record)
        else:
            filtered_records = []
            duplicate_records = []
                
        return filtered_records, duplicate_records
    
    def update_transactions(self, transactions: AllTransactionsTable) -> None:
        filtered_records, duplicate_records = self.filter_transactions(transactions)
        
        if duplicate_records:   
            logger.warning(f"{len(duplicate_records)} duplicate records found")
            
        if not filtered_records:
            logger.warning("No records to insert into the transactions table")
            return
        
        with self.batch_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions_db.add_records(filtered_records)
            
            logger.info(f"Inserted {len(filtered_records)} records into the transactions table")
            
    def update_monthly_results(self, transactions: AllTransactionsTable) -> None:
        transactions_cleaned = self.data_validation_service.delete_double_transactions(transactions)
        
        if not transactions_cleaned:
            logger.warning("No transactions to process")
            return
        
        user_id = self.user_session_service.current_user_id
        
        # Get and validate monthly results
        monthly_results = self.data_processing_service.get_monthly_results(transactions_cleaned)
        monthly_results = self.data_validation_service.validate_monthly_results(monthly_results) # TODO: Validate monthly results
        
        # Add user_id and year_month in str format to the monthly results
        monthly_results.year_months = monthly_results.year_months.astype(str)
        monthly_results.user_id = self.user_session_service.current_user_id 
        
        # Filter monthly results to avoid duplicates
        filtered_records, duplicate_records = self.filter_monthly_results(monthly_results)
        
        if duplicate_records:
            logger.warning(f"{len(duplicate_records)} duplicate records found")
            
        if not filtered_records:
            logger.warning("No records to insert into the monthly_results table")
            return
        
        with self.batch_conn() as conn:
            monthly_results_db = MonthlyResultDBService(conn)
            
            monthly_results_db.add_records(filtered_records)
            
            logger.info(f"Inserted {len(filtered_records)} records into the monthly_results table")
            
    def get_transactions(self) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions = transactions_db.get_transactions(user_id)
            
            return pd.DataFrame(transactions) if transactions else pd.DataFrame()
        
    def get_monthly_results(self) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            monthly_results_db = MonthlyResultDBService(conn)
            
            return monthly_results_db.get_monthly_results(user_id)
    
    def get_financial_analysis(self) -> dict:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            monthly_results_db = MonthlyResultDBService(conn)
            
            total_savings = monthly_results_db.get_total_savings(user_id)
            avg_income_per_month = monthly_results_db.get_avg_income_per_month(user_id)
            avg_withdrawal_per_month = monthly_results_db.get_avg_withdrawal_per_month(user_id)

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