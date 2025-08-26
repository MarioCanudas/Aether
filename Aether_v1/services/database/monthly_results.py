from typing import Optional, List, Dict, Any, Set
from models.records import MonthlyResultRecord
from .base_db import BaseDBService

class MonthlyResultDBService(BaseDBService):
    # Table information
    table_name = 'monthly_results'
    allowed_columns = {'monthly_result_id', 'user_id', 'year_month', 'initial_balance', 'total_income', 'total_withdrawal', 'savings', 'last_calculated_at'}
    
    # Column names
    id_col = 'monthly_result_id'
    user_id = 'user_id'
    year_month = 'year_month'
    initial_balance = 'initial_balance'
    total_income = 'total_income'
    total_withdrawal = 'total_withdrawal'
    savings = 'savings' 
    last_calculated_at = 'last_calculated_at'
    
    def get_monthly_results(
        self, 
        user_id: int, 
        columns: Optional[List[str]] = None
    ) -> List[MonthlyResultRecord]:
        if columns:
            columns = self._validate_columns(columns)
            query = f"""SELECT {', '.join(columns)} FROM {self.table_name}"""
        else:
            query = f"""SELECT * FROM {self.table_name}"""
        
        query += f" WHERE user_id = %(user_id)s"
        
        return self.execute_query(query, params= {'user_id': user_id}, fetch= 'all', dict_cursor= True)
    
    def add_records(self, records: List[Dict[str, Any]]) -> None:
        if not records:
            return
        
        record_columns = list(records[0].keys())
        
        with self.transaction():            
            query = f"""
                INSERT INTO {self.table_name} ({', '.join(record_columns)})
                VALUES (
                    {', '.join(f'%({col})s' for col in record_columns)}
                )
            """
            
            self.execute_query(query, params= records, batch= True)  
    
    def get_total_savings(self, user_id: int) -> float:
        query = f"""
            SELECT SUM({self.savings}) FROM {self.table_name}
            WHERE user_id = %(user_id)s
        """
        
        result = self.execute_query(query, params= {'user_id': user_id}, fetch= 'one')
        
        return result[0] if result else 0
    
    def get_avg_income_per_month(self, user_id: int) -> float:
        query = f"""
            SELECT AVG({self.total_income}) FROM {self.table_name}
            WHERE user_id = %(user_id)s
        """
        
        result = self.execute_query(query, params= {'user_id': user_id}, fetch= 'one')
        
        return result[0] if result else 0
    
    def get_avg_withdrawal_per_month(self, user_id: int) -> float:
        query = f"""
            SELECT AVG({self.total_withdrawal}) FROM {self.table_name}
            WHERE user_id = %(user_id)s
        """
        
        result = self.execute_query(query, params= {'user_id': user_id}, fetch= 'one')
        
        return result[0] if result else 0
    
    def get_existing_keys(self, all_params: Dict[str, str | int]) -> Set[str]:
        query_values = ', '.join(f'%({key})s::date' for key in all_params.keys() if key != 'user_id')
        
        query = f"""
            SELECT {self.year_month}
            FROM {self.table_name}
            WHERE {self.user_id} = %(user_id)s
            AND {self.year_month} IN ({query_values})   
        """
        
        result = self.execute_query(query, params= all_params, fetch= 'all')
        
        #to_str = lambda x: x[0].strftime('%Y-%m-%d') if hasattr(x[0], 'strftime') else x[0]
        
        return set(result for result in result) if result else set()