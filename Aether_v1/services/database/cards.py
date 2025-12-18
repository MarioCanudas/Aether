from models.cards import Card
from .base_db import BaseDBService

class CardsDBService(BaseDBService):
    # Table information
    table_name: str = 'cards'
    allowed_columns: set[str] = {'card_id', 'user_id', 'card_name', 'card_bank', 'statement_type'}
    
    # Column names
    id_col: str = 'card_id'
    user_id: str = 'user_id'
    card_name: str = 'card_name'
    card_bank: str = 'card_bank'
    statement_type: str = 'statement_type'
    
    def add_card(self, card: Card) -> None:
        with self.transaction():
            query = """
                INSERT INTO cards ({self.user_id}, {self.card_name}, {self.card_bank}, {self.statement_type})
                VALUES (%(user_id)s, %(card_name)s, %(card_bank)s, %(statement_type)s)
            """
            
            self.execute_query(query, params= card.model_dump())
            
    def get_cards(self, user_id: int) -> list[Card]:
        query = f"""SELECT * FROM cards WHERE {self.user_id} = %(user_id)s"""
        
        result = self.execute_query(query, params= {'user_id': user_id}, fetch= 'all', dict_cursor= True)
        
        if result and isinstance(result, list):
            return [Card(**r) for r in result if isinstance(r, dict)]
        return []
    
    def get_card_by_id(self, user_id: int, card_id: int) -> Card | None:
        query = f"""SELECT * FROM cards WHERE {self.user_id} = %(user_id)s AND {self.id_col} = %(card_id)s"""
        
        result = self.execute_query(query, params= {'user_id': user_id, 'card_id': card_id}, fetch= 'one', dict_cursor= True)
        
        return Card(**result) if result and isinstance(result, dict) else None
    
    def get_card_name(self, card_id: int) -> str | None:
        query = f"""SELECT {self.card_name} FROM cards WHERE {self.id_col} = %(card_id)s"""
        
        result = self.execute_query(query, params= {'card_id': card_id}, fetch= 'one')
        
        return result[0] if result and isinstance(result, tuple) else None
