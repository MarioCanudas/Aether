import pandas as pd
from io import BytesIO
from typing import List, Tuple, Dict, Any, Optional
import logging
from services import (
    StatementDataExtractionService,
    DataProcessingService, 
    DataValidationService,
    TransactionsDBService,
    CardsDBService
)
from models.cards import Card
from models.tables import AllTransactionsTable
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class UploadStatementsController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.data_validation_service = DataValidationService()
        
    def process_uploaded_files(self, uploaded_files: list[BytesIO], card: Optional[Card] = None) -> AllTransactionsTable:
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
        if card:
            all_transactions_df['card_id'] = card.card_id
        else:
            all_transactions_df['card_id'] = None
         
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
    
    def upload_transactions(self, transactions: AllTransactionsTable) -> None:
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
            
    def get_cards(self) -> List[str]:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)
            
            cards = cards_db.get_cards(self.user_id)
            
            return [card.card_name for card in cards]
        
    def get_card_by_name(self, card_name: str) -> Card:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)
            
            card_id = cards_db.find_id(card_name= card_name, user_id= self.user_id)
            
            return cards_db.get_card_by_id(self.user_id, card_id)