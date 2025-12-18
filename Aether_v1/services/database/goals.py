from datetime import date
from typing import Literal, Any
from models.goals import Goal
from .base_db import BaseDBService

class GoalsDBService(BaseDBService):
    # Table information
    table_name: str = 'goals'
    allowed_columns: set[str] = {'goal_id', 'user_id', 'type', 'category_id', 'name', 'amount', 'added_amount', 
                       'created_at', 'updated_at', 'start_date', 'end_date', 'status', 'related_transaction_type'}
    
    # Column names
    id_col: str = 'goal_id'
    user_id: str = 'user_id'
    type: str = 'type'
    category_id: str = 'category_id'
    name: str = 'name'
    amount: str = 'amount'
    added_amount: str = 'added_amount'
    created_at: str = 'created_at'
    updated_at: str = 'updated_at'
    start_date: str = 'start_date'
    end_date: str = 'end_date'
    status: str = 'status'
    related_transaction_type: str = 'related_transaction_type'
    
    def add_goal(self, goal: Goal) -> None:
        with self.transaction():
            query = """
                INSERT INTO goals (user_id, type, related_transaction_type, category_id, name, amount, start_date, end_date)
                VALUES (%(user_id)s, %(type)s, %(related_transaction_type)s, %(category_id)s, %(name)s, %(amount)s, %(start_date)s, %(end_date)s)
            """
            
            self.execute_query(query, params= goal.to_record())
            
    def get_goals(
            self,
            user_id: int,
            status: Literal['current', 'past'] | None = None,
            columns: list[str] | None = None,
            order_by: Literal['start_date', 'end_date'] | None = None,
            order: Literal['asc', 'desc'] | None = None,
            show_categories_names: bool | None = False
        ) -> list[dict[str, Any]]:
        if columns:
            columns = self._validate_columns(columns)
            columns = [f'g.{col}' for col in columns]
            if show_categories_names:
                columns.append('c.name AS category')
            
            query = f"""
                SELECT {', '.join(columns)} FROM {self.table_name} AS g
            """
        else:
            query = f"""
                SELECT * FROM {self.table_name} AS g
            """
            
        if show_categories_names:
            query += f" LEFT JOIN categories AS c ON g.{self.category_id} = c.{self.category_id}"
            
        query += f" WHERE g.{self.user_id} = %(user_id)s"
        
        params: dict[str, Any] = {'user_id': user_id}
        
        if status:
            query += f" AND g.{self.end_date} >= %(today)s" if status == 'current' else f" AND g.{self.end_date} < %(today)s"
            params['today'] = date.today()
            
        if order_by:
            query += f" ORDER BY g.{order_by}" if not order else f" ORDER BY g.{order_by} {order.upper()}"
        
        result = self.execute_query(query, params= params, fetch= 'all', dict_cursor= True)
        
        if result and isinstance(result, list):
            return [r for r in result if isinstance(r, dict)]
        return []
