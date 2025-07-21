import pandas as pd
from io import BytesIO
from functools import cache
from typing import Dict, Any, Literal, List
from models import DocumentProcessingFacade, TableProcessingFacade, DataProcessingFacade

class TransactionExtractionService:
    """
    The TransactionExtractionService class is responsible for extracting the transactions from a PDF file.
    It is the only service that uses the models and facades from the models package.
    
    Args:
        file (str | BytesIO): The path to the PDF file or a BytesIO object.
        
    Attributes:
        file (str | BytesIO): The path to the PDF file or a BytesIO object.
        document_processor (DocumentProcessingFacade | None): The document processor.
        table_processor (TableProcessingFacade | None): The table processor.
        data_processor (DataProcessingFacade | None): The data processor.
    """
    def __init__(self, file: str | BytesIO):
        self.file = file
        self.document_processor: DocumentProcessingFacade | None = None
        self.table_processor: TableProcessingFacade | None = None
        self.data_processor: DataProcessingFacade | None = None
        
    def _set_document_processor(self) -> None:
        self.document_processor = DocumentProcessingFacade(self.file)
        
    @cache
    def get_corrected_extracted_words(self) -> pd.DataFrame:
        if self.document_processor is not None:
            return self.document_processor.get_corrected_extracted_words()
        else:
            raise ValueError("Document processor not set")
    
    @cache
    def get_statement_properties(self) -> dict:
        if self.document_processor is not None:
            return self.document_processor.get_statement_properties()
        else:
            raise ValueError("Document processor not set")
    
    def _set_table_processor(self) -> None:
        corrected_extracted_words = self.get_corrected_extracted_words()
        statement_properties = self.get_statement_properties()
        
        self.table_processor = TableProcessingFacade(corrected_extracted_words, statement_properties)
    
    @cache
    def get_reconstructed_table(self) -> pd.DataFrame:
        if self.table_processor is not None:
            return self.table_processor.reconstruct_table()
        else:
            raise ValueError("Table processor not set")
    
    def _set_data_processor(self) -> None:
        corrected_extracted_words = self.get_corrected_extracted_words()
        reconstructed_table = self.get_reconstructed_table()
        statement_properties = self.get_statement_properties()
        
        self.data_processor = DataProcessingFacade(corrected_extracted_words, reconstructed_table, statement_properties)
        
    def _set_all_processors(self) -> None:
        if not self.document_processor:
            self._set_document_processor()
        
        if not self.table_processor:
            self._set_table_processor()
        
        if not self.data_processor:
            self._set_data_processor()
            
    @cache
    def get_transactions_from_pdf(self, return_type: Literal['dataframe', 'records'] = 'dataframe') -> pd.DataFrame | List[Dict[str, Any]]:
        """
        Get the transactions from the PDF file, using the models and facades from the models package.
        
        Args:
            return_type (Literal['dataframe', 'records']): The type of return.
            
        Returns:
            pd.DataFrame | List[Dict[str, Any]]: The transactions.
            
        Raises:
            ValueError: If the return type is invalid.
        """
        self._set_all_processors()
        
        transactions = self.data_processor.get_transactions()
        
        transactions['bank'] = self.get_statement_properties()['bank']
        transactions['statement_type'] = self.get_statement_properties()['statement_type']
        transactions['filename'] = self.file.name if isinstance(self.file, BytesIO) else self.file
        
        if return_type == 'dataframe':
            return transactions
        elif return_type == 'records':
            return transactions.to_dict(orient='records')
        else:
            raise ValueError("Invalid return type")
    
    @cache
    def get_metadata(self) -> Dict[str, Any] | None:
        """
        Get the metadata from the PDF file, using the models and facades from the models package.
        
        Returns:
            Dict[str, Any] | None: The metadata.
        """
        self._set_all_processors()
        
        properties = self.get_statement_properties()
        
        bank = properties['bank']
        statement_type = properties['statement_type']
        period = self.data_processor.get_period()
        initial_balance, final_balance = self.data_processor.get_balances()
        
        return {
            'bank': bank,
            'statement_type': statement_type,
            'period': period,
            'initial_balance': initial_balance,
            'final_balance': final_balance
        }