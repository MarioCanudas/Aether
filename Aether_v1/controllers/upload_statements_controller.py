import pandas as pd
from io import BytesIO
from typing import List, Dict, Optional, Any
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
from models.transactions import Transaction, DuplicateResult, FilteredTransactionsResult
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class UploadStatementsController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.data_validation_service = DataValidationService()
        self.dt_service = DuplicateTreatmentService()
        
    def process_uploaded_files(self, uploaded_files: list[BytesIO], card: Optional[Card] = None) -> List[Transaction]:
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
        all_transactions_df['duplicate_potential_state'] = False
        all_transactions_df['transaction_id'] = None
        
        if card:
            all_transactions_df['card_id'] = card.card_id
        else:
            all_transactions_df['card_id'] = None
                     
        return [Transaction(**r) for r in all_transactions_df.to_dict(orient='records')]
    
    async def filter_transactions(self, transactions: List[Transaction]) -> FilteredTransactionsResult:
        clean_transactions, duplicated_transactions = self.dt_service.eliminate_credit_and_debit_duplicates(transactions)
        
        with self.quick_read_conn() as conn:
            duplicates_results: List[DuplicateResult] = await self.dt_service.detect_duplicates(conn, self.user_id, clean_transactions)
            
        filtered_transactions_result = FilteredTransactionsResult(duplicated= duplicated_transactions)
            
        for result in duplicates_results:
            if result.has_exact_duplicates:
                filtered_transactions_result.duplicated.append(result.transaction)
            elif result.has_potential_duplicates:
                filtered_transactions_result.potential_duplicates_to_upload.append(result.transaction)
                filtered_transactions_result.potential_duplicates_to_modify.extend(result.potential_duplicates)
            else:
                filtered_transactions_result.clean.append(result.transaction)
        
        return filtered_transactions_result
    
    def upload_transactions(self, filtered_transactions_result: FilteredTransactionsResult) -> None:
        with self.batch_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            if len(filtered_transactions_result.potential_duplicates_to_modify) > 0:
                transactions_db.update_transactions(filtered_transactions_result.potential_duplicates_to_modify_unique)
                
            transactions_to_upload = filtered_transactions_result.potential_duplicates_to_upload + filtered_transactions_result.clean
            
            if len(transactions_to_upload) > 0:
                transactions_db.add_records(transactions_to_upload)
            
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