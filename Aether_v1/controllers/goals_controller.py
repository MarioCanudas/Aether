import pandas as pd
from datetime import date
from streamlit import session_state
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List, Optional
from models.categories import GoalType
from models.dates import PeriodRange
from models.financial import Goal, GoalInfo
from .base_controller import BaseController

class GoalsController(BaseController):
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
    def get_goal_types() -> List[str]:
        return [goal_type.value for goal_type in GoalType]
    
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
    
    def add_goal(self, new_goal: Goal) -> None:
        with self.batch_scope() as db:
            db.insert_record('goals', new_goal.to_record())
            
    def get_goal_info(self, goal_name: str) -> GoalInfo:
        return GoalInfo(
            name= goal_name,
            type= GoalType.BUDGET.value,
            category= 'test',
            amount= 100,
            added_amount= 50,
            remaining= 50,
            expenses= 0,
            start_date= date(2025, 1, 1),
            end_date= date(2025, 1, 31),
            achived= None,
        )
            
    def process_goal_table(self, goal_table: pd.DataFrame) -> pd.DataFrame:
        if goal_table.empty:
            return goal_table
        
        categories_map = self.get_categories_map()
        
        goal_table['category'] = goal_table['category_id'].apply(lambda x: categories_map[x])
        goal_table['start_date'] = goal_table['start_date'].dt.strftime('%Y/%m/%d')
        goal_table['end_date'] = goal_table['end_date'].dt.strftime('%Y/%m/%d')
        
        return goal_table[['name', 'type', 'category', 'amount', 'start_date', 'end_date']]
            
    def get_current_goals(self) -> pd.DataFrame:
        query = """
            SELECT name, type, category_id, amount, added_amount, start_date, end_date FROM goals 
            WHERE user_id = %(user_id)s 
            AND end_date >= %(today)s
        """
        
        with self.quick_read_scope() as db:
            df = db.custom_query(query, {'user_id': session_state.user_id, 'today': date.today()}, value_format= 'dataframe')
            
            return self.process_goal_table(df)
        
    def get_current_goals_names(self) -> List[str]:
        query = """
            SELECT name FROM goals 
            WHERE user_id = %(user_id)s 
            AND achived IS NULL
            ORDER BY start_date DESC
        """
        
        with self.quick_read_scope() as db:
            result =  db.custom_query(query, {'user_id': session_state.user_id}, value_format= 'tuple')
            
            return [name[0] for name in result]
        
    def get_past_goals(self) -> pd.DataFrame:
        query = """
            SELECT name, type, category_id, amount, added_amount, start_date, end_date, achived FROM goals 
            WHERE user_id = %(user_id)s 
            AND end_date < %(today)s
        """
        
        with self.quick_read_scope() as db:
            df = db.custom_query(query, {'user_id': session_state.user_id, 'today': date.today()}, value_format= 'dataframe')
            
            return self.process_goal_table(df)
        