import pandas as pd
from io import BytesIO
from typing import List, Tuple, Literal
import logging
from services import (
    StatementDataExtractionService,
    DataProcessingService, 
    FinancialAnalysisService,
    PlottingService, DataValidationService, DatabaseService
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
        
        return AllTransactionsTable(df=all_transactions_df)
    
    def filter_transactions(
            self, 
            db_service: DatabaseService, 
            all_transactions: AllTransactionsTable,
            value_format: Literal['dataframe', 'records'] = 'records'
        ) -> Tuple[List[TransactionRecord], List[TransactionRecord]]:
        user_id = self.user_session_service.current_user_id
        
        transactions_cleaned = self.data_validation_service.delete_double_transactions(all_transactions)
        records = transactions_cleaned.records
        
        # Batch processing optimization
        if records:
            # Get existing transactions in a single query
            existing_keys = self.data_validation_service.get_existing_transaction_keys(
                db_service, 
                records, 
                user_id
            )
            
            filtered_records = []
            duplicate_records = []
            
            for record in records:
                # Create unique key for comparison
                key = (
                    record['filename'],
                    record['date'].strftime('%Y-%m-%d') if hasattr(record['date'], 'strftime') else record['date'],
                    record['amount'],
                    record['description']
                )
                
                if key in existing_keys:
                    duplicate_records.append(record)
                else:
                    filtered_records.append(record)
        else:
            filtered_records = []
            duplicate_records = []
                
        if value_format == 'dataframe':
            filtered_records = pd.DataFrame(filtered_records)
            duplicate_records = pd.DataFrame(duplicate_records)
                
        return filtered_records, duplicate_records
    
    def filter_monthly_results(
            self,
            db_service: DatabaseService,
            monthly_results: MonthlyResultsTable,
            value_format: Literal['dataframe', 'records'] = 'records'
        ) -> Tuple[List[MonthlyResultRecord], List[MonthlyResultRecord]]:
        user_id = self.user_session_service.current_user_id
        records = monthly_results.records
            
        # Batch processing optimization
        if records:
            # Get existing monthly results in a single query
            existing_keys = self.data_validation_service.get_existing_monthly_result_keys(
                db_service, 
                records, 
                user_id
            )
            
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
                
        if value_format == 'dataframe':
            filtered_records = pd.DataFrame(filtered_records)
            duplicate_records = pd.DataFrame(duplicate_records)
                
        return filtered_records, duplicate_records
    
    def add_transaction(self, transaction: TransactionRecord) -> None:
        with self.batch_scope() as db:
            db.insert_record('transactions', transaction)
            logger.info(f"Inserted {transaction} into the transactions table")
    
    def update_transactions(self, transactions: AllTransactionsTable) -> None:
        with self.batch_scope() as db:
            filtered_records, duplicate_records = self.filter_transactions(db, transactions)
                    
            if duplicate_records:   
                logger.warning(f"{len(duplicate_records)} duplicate records found")
                
            if not filtered_records:
                logger.warning("No records to insert into the transactions table")
                return
            
            db.insert_multiple_records('transactions', filtered_records)
            logger.info(f"Inserted {len(filtered_records)} records into the transactions table")
            
    def update_monthly_results(self, transactions: AllTransactionsTable) -> None:
        transactions_cleaned = self.data_validation_service.delete_double_transactions(transactions)
        
        # Get and validate monthly results
        monthly_results = self.data_processing_service.get_monthly_results(transactions_cleaned)
        monthly_results = self.data_validation_service.validate_monthly_results(monthly_results) # TODO: Validate monthly results
        
        # Add user_id and year_month in str format to the monthly results
        monthly_results.year_months = monthly_results.year_months.astype(str)
        monthly_results.user_id = self.user_session_service.current_user_id 
        
        with self.batch_scope() as db:
            # Filter monthly results to avoid duplicates
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
            # Ensure date is in datetime format
            transactions['date'] = pd.to_datetime(transactions['date'])
            
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