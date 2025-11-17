from typing import List
from models.cards import Card
from .base_db import BaseDBService

class CardsDBService(BaseDBService):
    # Table information
    table_name = 'cards'
    allowed_columns = {'card_id', 'user_id', 'name', 'bank', 'statement_type'}
    
    # Column names
    id_col = 'card_id'
    user_id = 'user_id'
    name = 'name'
    bank = 'bank'
    statement_type = 'statement_type'
    
    def add_card(self, card: Card) -> None:
        with self.transaction():
            query = """
                INSERT INTO cards (user_id, name, bank, statement_type)
                VALUES (%(user_id)s, %(name)s, %(bank)s, %(statement_type)s)
            """
            
            self.execute_query(query, params= card.model_dump())
            
    def get_cards(self, user_id: int) -> List[Card]:
        query = """SELECT * FROM cards WHERE user_id = %(user_id)s"""
        
        result = self.execute_query(query, params= {'user_id': user_id}, fetch= 'all', dict_cursor= True)
        
        return [Card(**r) for r in result]
    
    def get_card_by_id(self, user_id: int, card_id: int) -> Card:
        query = """SELECT * FROM cards WHERE user_id = %(user_id)s AND card_id = %(card_id)s"""
        
        result = self.execute_query(query, params= {'user_id': user_id, 'card_id': card_id}, fetch= 'one', dict_cursor= True)
        
        return Card(**result) if result else None