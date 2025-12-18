from typing import Any, cast
from models.templates import Template, TemplateType, TransactionDefaultValues, GoalDefaultValues
from .base_db import BaseDBService

class TemplatesDBService(BaseDBService):
    # Table information
    table_name: str = 'templates'
    allowed_columns: set[str] = {'template_id', 'user_id', 'card_id', 'template_name', 'template_description', 'template_type', 'default_values'}
    
    # Column names
    id_col: str = 'template_id'
    user_id: str = 'user_id'
    card_id: str = 'card_id'
    template_name: str = 'template_name'
    template_description: str = 'template_description'
    template_type: str = 'template_type'
    default_values: str = 'default_values'
    
    def get_templates_names(self, user_id: int, template_type: TemplateType) -> dict[str, int]:
        """
        Get the mapped names of the templates.
        
        >>> Parameters:
        user_id: int
        template_type: TemplateType
        
        >>> Returns:
        dict[str, int] - The mapped names of the templates with their ids.
        """
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE {self.user_id} IS NULL OR {self.user_id} = %(user_id)s
            AND {self.template_type} = %(template_type)s
        """
        
        result = self.execute_query(query, params={'user_id': user_id, 'template_type': template_type}, fetch= 'all', dict_cursor= True)
        
        if not result or not isinstance(result, list):
            return {}
        else:
            return {r[self.template_name]: r[self.id_col] for r in result if isinstance(r, dict)}
        
    def get_template(self, template_id: int) -> Template | None:
        query = f"""
            SELECT * FROM {self.table_name} WHERE {self.id_col} = %(template_id)s
        """
        
        result = self.execute_query(query, params= {'template_id': template_id}, fetch= 'one', dict_cursor= True)
        
        if not result or not isinstance(result, dict):
            return None
        else:
            del result[self.id_col]
            
            default_values: dict[str, Any] = result[self.default_values]

            if result[self.template_type] == TemplateType.TRANSACTION:
                result[self.default_values] = TransactionDefaultValues.from_dict(default_values)
            elif result[self.template_type] == TemplateType.GOAL:
                result[self.default_values] = GoalDefaultValues.from_dict(default_values)
            
        return Template(**result)
    
    def add_template(self, template: Template) -> None:
        with self.transaction():
            query = f"""
                INSERT INTO {self.table_name} ({self.user_id}, {self.template_name}, {self.template_description}, {self.template_type}, {self.default_values})
                VALUES (%(user_id)s, %(template_name)s, %(template_description)s, %(template_type)s, %(default_values)s)
            """
            
            self.execute_query(query, params= template.to_record())
            
    def update_template(self, template_id: int, updated_template: Template) -> None:
        with self.transaction():
            query = f"""
                UPDATE {self.table_name}
                SET {self.user_id} = %(user_id)s, {self.template_name} = %(template_name)s, {self.template_description} = %(template_description)s, {self.template_type} = %(template_type)s, {self.default_values} = %(default_values)s
                WHERE {self.id_col} = %(template_id)s
            """
            
            params: dict[str, Any] = {**cast(dict[str, Any], updated_template.to_record()), 'template_id': template_id}
            
            self.execute_query(query, params= params)
            
    def delete_template(self, template_id: int) -> None:
        with self.transaction():
            query = f"""
                DELETE FROM {self.table_name}
                WHERE {self.id_col} = %(template_id)s
            """
            
            self.execute_query(query, params= {'template_id': template_id})
