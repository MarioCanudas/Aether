from datetime import date
from typing import Literal, Optional, List, Dict, Any
from models.financial import Goal
from .base_db import BaseDBService

class GoalsDBService(BaseDBService):
    # Table information
    table_name = 'goals'
    allowed_columns = {'goal_id', 'user_id', 'type', 'category_id', 'name', 'amount', 'added_amount', 
                       'created_at', 'updated_at', 'start_date', 'end_date', 'achieved'}
    
    # Column names
    id_col = 'goal_id'
    user_id = 'user_id'
    type = 'type'
    category_id = 'category_id'
    name = 'name'
    amount = 'amount'
    added_amount = 'added_amount'
    created_at = 'created_at'
    updated_at = 'updated_at'
    start_date = 'start_date'
    end_date = 'end_date'
    achieved = 'achieved'
    
    def add_goal(self, goal: Goal) -> None:
        with self.transaction():
            query = """
                INSERT INTO goals (user_id, type, category_id, name, amount, start_date, end_date)
                VALUES (%(user_id)s, %(type)s, %(category_id)s, %(name)s, %(amount)s, %(start_date)s, %(end_date)s)
            """
            
            self.execute_query(query, params= goal.to_record())
            
    def get_goals(
            self,
            user_id: int,
            status: Optional[Literal['current', 'past']] = None,
            columns: Optional[List[str]] = None,
            order_by: Optional[Literal['start_date', 'end_date']] = None,
            order: Optional[Literal['asc', 'desc']] = None,
            show_categories_names: Optional[bool] = False
        ) -> List[Dict[str, Any]]:
        if columns:
            columns = self._validate_columns(columns)
            columns = [f'g.{col}' for col in columns]
            columns.append('c.name AS category') if show_categories_names else None
            
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
        
        params = {'user_id': user_id}
        
        if status:
            query += f" AND g.{self.end_date} >= %(today)s" if status == 'current' else f" AND g.{self.end_date} < %(today)s"
            params['today'] = date.today()
            
        if order_by:
            query += f" ORDER BY g.{order_by}" if not order else f" ORDER BY g.{order_by} {order.upper()}"
        
        return self.execute_query(query, params= params, fetch= 'all', dict_cursor= True)