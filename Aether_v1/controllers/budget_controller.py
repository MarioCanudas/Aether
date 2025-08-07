import pandas as pd
from datetime import date
from streamlit import session_state
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List, Optional
from models.dates import PeriodRange
from models.financial import Budget, BudgetInfo
from .base_controller import BaseController

class BudgetController(BaseController):
    def get_categories(self) -> List[str]:
        with self.quick_read_scope() as db:
            return db.get_unique_values('categories', 'name')
    
    def get_category_id(self, category: str) -> int:
        query = """
            SELECT id FROM categories WHERE name = %(category)s
        """
        
        with self.quick_read_scope() as db:
            return db.custom_query(query, {'category': category}, value_format= 'scalar')
        
    def get_categories_map(self) -> Dict[int, str]:
        query = """
            SELECT id, name FROM categories WHERE user_id IS NULL OR user_id = %(user_id)s
        """
        
        with self.quick_read_scope() as db:
            categories: List[Dict[str, Any]] =  db.custom_query(query, {'user_id': session_state.user_id}, value_format= 'dict')
            
            return {category['id']: category['name'] for category in categories}
    
    @staticmethod
    def get_period_ranges() -> List[str]:
        return [period_range.value for period_range in PeriodRange]
    
    @staticmethod   
    def get_end_date(start_date: date, period_range: str) -> Optional[date]:
        match period_range:
            case PeriodRange.WEEKLY.value:
                return start_date + relativedelta(weeks= 1)
            case PeriodRange.FORTNIGHTLY.value:
                return start_date + relativedelta(weeks= 2)
            case PeriodRange.MONTHLY.value:
                return start_date + relativedelta(months= 1)
            case PeriodRange.BIMONTHLY.value:
                return start_date + relativedelta(months= 2)
            case PeriodRange.QUARTERLY.value:
                return start_date + relativedelta(months= 3)
            case PeriodRange.SEMIANNUAL.value:
                return start_date + relativedelta(months= 6)
            case PeriodRange.ANNUAL.value:
                return start_date + relativedelta(years= 1)
            case PeriodRange.OTHER.value:
                return None
    
    def add_budget(self, new_budget: Budget) -> None:
        with self.batch_scope() as db:
            db.insert_record('budgets', new_budget.to_record())
            
    def get_budget_info(self, budget_name: str) -> BudgetInfo:
        return BudgetInfo(
            name= budget_name,
            category= 'test',
            amount= 100,
            added_amount= 50,
            remaining= 50,
            expenses= 0,
            start_date= date(2025, 1, 1),
            end_date= date(2025, 1, 31),
            achived= None,
        )
            
    def process_budget_table(self, budget_table: pd.DataFrame) -> pd.DataFrame:
        if budget_table.empty:
            return budget_table
        
        categories_map = self.get_categories_map()
        
        budget_table['category'] = budget_table['category_id'].apply(lambda x: categories_map[x])
        budget_table['start_date'] = budget_table['start_date'].dt.strftime('%Y/%m/%d')
        budget_table['end_date'] = budget_table['end_date'].dt.strftime('%Y/%m/%d')
        
        return budget_table[['name', 'category', 'amount', 'start_date', 'end_date']]
            
    def get_current_budgets(self) -> pd.DataFrame:
        query = """
            SELECT name, category_id, amount, added_amount, start_date, end_date FROM budgets 
            WHERE user_id = %(user_id)s 
            AND end_date >= %(today)s
        """
        
        with self.quick_read_scope() as db:
            df = db.custom_query(query, {'user_id': session_state.user_id, 'today': date.today()}, value_format= 'dataframe')
            
            return self.process_budget_table(df)
        
    def get_current_budgets_names(self) -> List[str]:
        query = """
            SELECT name FROM budgets 
            WHERE user_id = %(user_id)s 
            AND achived IS NULL
            ORDER BY start_date DESC
        """
        
        with self.quick_read_scope() as db:
            result =  db.custom_query(query, {'user_id': session_state.user_id}, value_format= 'tuple')
            
            return [name[0] for name in result]
        
    def get_past_budgets(self) -> pd.DataFrame:
        query = """
            SELECT name, category_id, amount, added_amount, start_date, end_date, achived FROM budgets 
            WHERE user_id = %(user_id)s 
            AND end_date < %(today)s
        """
        
        with self.quick_read_scope() as db:
            df = db.custom_query(query, {'user_id': session_state.user_id, 'today': date.today()}, value_format= 'dataframe')
            
            return self.process_budget_table(df)
        