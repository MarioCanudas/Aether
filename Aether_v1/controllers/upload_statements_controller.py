import pandas as pd
from io import BytesIO
from typing import List, Tuple, Dict, Any, Optional
import logging
from services import (
    StatementDataExtractionService,
    DataProcessingService, 
    DataValidationService,
    TransactionsDBService,
    CardsDBService,
    DuplicateTreatmentService
)
from models.cards import Card
from models.tables import AllTransactionsTable
from models.transactions import Transaction
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class UploadStatementsController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.data_validation_service = DataValidationService()
        self.dt_service = DuplicateTreatmentService()
        
    def process_uploaded_files(self, uploaded_files: list[BytesIO], card: Optional[Card] = None) -> AllTransactionsTable:
        all_transactions = []
        
        for uploaded_file in uploaded_files:
            # Set the transaction extraction service per file
            statement_data_extraction_service = StatementDataExtractionService(self.user_id, uploaded_file)
            transactions_table = statement_data_extraction_service.get_transactions()
            metadata = statement_data_extraction_service.metadata_extractor.get_metadata()
            
            validated_transactions = self.data_validation_service.validate_transactions(transactions_table, metadata)
            
            all_transactions.append(validated_transactions.df)
                
        all_transactions_df = pd.concat(all_transactions, ignore_index=True)
        all_transactions_df['user_id'] = self.user_session_service.current_user_id
        all_transactions_df['category_id'] = None
        if card:
            all_transactions_df['card_id'] = card.card_id
        else:
            all_transactions_df['card_id'] = None
         
        return AllTransactionsTable(df=all_transactions_df)
    
    def filter_transactions(self, all_transactions: AllTransactionsTable) -> Tuple[List[Transaction], List[Transaction]]:
        duplicated, filtered = self.dt_service.eliminate_credit_and_debit_duplicates(all_transactions)
        
        if not filtered:
            return duplicated, []
        
        with self.quick_read_conn() as conn:
            transaction_db = TransactionsDBService(conn)

            period = self.dt_service.get_transactions_period(filtered)
            existing_keys = transaction_db.get_existing_keys(self.user_id, period)
            
        to_delete: List[Transaction] = []
        # Batch processing optimization
        if filtered:
            for transaction in filtered:
                # Create unique key for comparison
                key = (
                    transaction.date.strftime('%Y-%m-%d'),
                    transaction.amount,
                    transaction.description,
                    transaction.bank.value,
                    transaction.statement_type.value
                )
                
                if key in existing_keys:
                    duplicated.append(transaction)
                    to_delete.append(transaction)
                    
        if to_delete:
            for transaction in to_delete:
                filtered.remove(transaction)
                
        return filtered, duplicated
    
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