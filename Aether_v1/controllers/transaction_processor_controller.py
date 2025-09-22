import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import asyncio
from typing import List, Tuple, Dict, Any
import logging
from services import (
    StatementDataExtractionService,
    DataProcessingService, 
    FinancialAnalysisService,
    PlottingService, 
    DataValidationService,
    TransactionsDBService
)
from models.financial import SummaryMetrics, FinancialSummary
from models.tables import AllTransactionsTable, MonthlyResultsTable
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
            
    def get_transactions(self) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions = transactions_db.get_transactions(user_id)
            
            return pd.DataFrame(transactions) if transactions else pd.DataFrame()
        
    def get_monthly_results(self) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions = transactions_db.get_transactions(user_id)
            
            all_transactions = AllTransactionsTable(df = pd.DataFrame(transactions))
            monthly_results: MonthlyResultsTable = self.data_processing_service.get_monthly_results(all_transactions)
            
            monthly_results.year_months = monthly_results.year_months.astype(str)
            
            return monthly_results.df
        
    async def get_summary_metrics(self) -> SummaryMetrics:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions = transactions_db.get_transactions(self.user_id)
            
            all_transactions = AllTransactionsTable(df = pd.DataFrame(transactions))
            monthly_results: MonthlyResultsTable = self.data_processing_service.get_monthly_results(all_transactions)
            
            monthly_results.year_months = monthly_results.year_months.astype(str)
            
            async with asyncio.TaskGroup() as tg:
                total_savings = tg.create_task(
                    monthly_results.get_total_savings()
                )
                avg_income_per_month = tg.create_task(
                    monthly_results.get_avg_income_per_month()
                )
                avg_withdrawal_per_month = tg.create_task(
                    monthly_results.get_avg_withdrawal_per_month()
                )
            
            return SummaryMetrics(
                total_savings= total_savings.result(),
                avg_income_per_month= avg_income_per_month.result(),
                avg_withdrawal_per_month= avg_withdrawal_per_month.result()
            )
            
    def get_financial_summary(self) -> FinancialSummary:
        summary_metrics = asyncio.run(self.get_summary_metrics())
        
        label = self.financial_analysis_service.get_financial_status_label(summary_metrics)
        tips = self.financial_analysis_service.get_financial_tips(label)

        return FinancialSummary(
            summary_metrics= summary_metrics,
            label= label.value,
            tips= tips
        )
        
    def get_donut_score_chart(self) -> plt.Figure:
        summary_metrics = asyncio.run(self.get_summary_metrics())
        label = self.financial_analysis_service.get_financial_status_label(summary_metrics)
        donut_config = self.plotting_service.get_savings_donut_chart_config(label)
        
        return self.plotting_service.get_plot_savings_donut_chart(donut_config)
        