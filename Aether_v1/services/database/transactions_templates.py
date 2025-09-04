from typing import List, Dict
from models.templates import TransactionTemplate
from .base_db import BaseDBService

class TransactionsTemplatesDBService(BaseDBService):
    # Table information
    table_name = 'transactions_templates'
    allowed_columns = {'transaction_template_id', 'user_id', 'template_name', 'template_description', 
                       'transaction_date', 'transaction_type', 'transaction_amount', 'transaction_category_id',
                       'transaction_description'}
    
    # Column names
    id_col = 'template_id'
    user_id = 'user_id'
    template_name = 'template_name'
    template_description = 'template_description'
    transaction_date = 'transaction_date'
    transaction_type = 'transaction_type'
    transaction_amount = 'transaction_amount'
    transaction_category_id = 'transaction_category_id'
    transaction_description = 'transaction_description'
    
    def get_templates_names(self, user_id: int) -> Dict[str, int]:
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE {self.user_id} IS NULL OR {self.user_id} = %(user_id)s
        """
        
        result = self.execute_query(query, params={'user_id': user_id}, fetch= 'all', dict_cursor= True)
        
        if not result:
            return {}
        else:
            return {r[self.template_name]: r[self.id_col] for r in result}
        
    def get_template(self, template_id: int) -> TransactionTemplate | None:
        query = f"""
            SELECT * FROM {self.table_name} WHERE {self.id_col} = %(template_id)s
        """
        
        result = self.execute_query(query, params= {'template_id': template_id}, fetch= 'one', dict_cursor= True)
        
        if not result:
            return None
        else:
            del result[self.id_col]
            
        return TransactionTemplate(**result)
    
    def add_template(self, template: TransactionTemplate) -> None:
        with self.transaction():
            query = f"""
                INSERT INTO {self.table_name} ({self.user_id}, {self.template_name}, {self.template_description}, {self.transaction_date}, {self.transaction_type}, {self.transaction_amount}, {self.transaction_category_id}, {self.transaction_description})
                VALUES (%(user_id)s, %(template_name)s, %(template_description)s, %(transaction_date)s, %(transaction_type)s, %(transaction_amount)s, %(transaction_category_id)s, %(transaction_description)s)
            """
            
            self.execute_query(query, params= template.model_dump())
            
    def update_template(self, template_id: int, new_template: TransactionTemplate) -> None:
        with self.transaction():
            query = f"""
                UPDATE {self.table_name}
                SET {self.user_id} = %(user_id)s, {self.template_name} = %(template_name)s, {self.template_description} = %(template_description)s, {self.transaction_date} = %(transaction_date)s, {self.transaction_type} = %(transaction_type)s, {self.transaction_amount} = %(transaction_amount)s, {self.transaction_category_id} = %(transaction_category_id)s, {self.transaction_description} = %(transaction_description)s
                WHERE {self.id_col} = %(template_id)s
            """
            
            params = {**new_template.model_dump(), 'template_id': template_id}
            
            self.execute_query(query, params= params)
            
    def delete_template(self, template_id: int) -> None:
        with self.transaction():
            query = f"""
                DELETE FROM {self.table_name}
                WHERE {self.id_col} = %(template_id)s
            """
            
            self.execute_query(query, params= {'template_id': template_id})
            
        