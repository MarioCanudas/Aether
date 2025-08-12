import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import List, Optional
from services import CategoryDBService, GoalsDBService
from models.categories import GoalType
from models.dates import PeriodRange
from models.financial import Goal, GoalInfo
from .base_controller import BaseController

class GoalsController(BaseController):
    def get_categories(self) -> List[str]:
        with self.quick_read_conn() as conn:
            categories_db = CategoryDBService(conn)
            
            return categories_db.get_categories_by_user(self.user_id)
    
    def get_category_id(self, category: str) -> int:
        with self.quick_read_conn() as conn:
            categories_db = CategoryDBService(conn)
            
            return categories_db.find_id(name= category)
        
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
        with self.session_conn() as conn:
            goals_db = GoalsDBService(conn)
            
            goals_db.add_goal(new_goal)
    
    def get_current_goals_names(self) -> List[str]:
        with self.quick_read_conn() as conn:
            goals_db = GoalsDBService(conn)
            
            return goals_db.get_unique_values('name', user_id= self.user_id)
            
    def get_current_goals(self) -> pd.DataFrame:
        with self.quick_read_conn() as conn:
            goals_db = GoalsDBService(conn)
            
            goals = goals_db.get_goals(
                user_id= self.user_id,
                status= 'current',
                columns= ['name', 'type', 'amount', 'start_date', 'end_date'],
                order_by= 'start_date',
                order= 'asc',
                show_categories_names= True
            )
            
            return pd.DataFrame(goals) if goals else pd.DataFrame()
        
    def get_past_goals(self) -> pd.DataFrame:
        with self.quick_read_conn() as conn:
            goals_db = GoalsDBService(conn)
            
            goals = goals_db.get_goals(
                user_id= self.user_id,
                status= 'past',
                columns= ['name', 'type', 'amount', 'start_date', 'end_date', 'achieved'],
                order_by= 'end_date',
                order= 'desc',
                show_categories_names= True
            )
            
            return pd.DataFrame(goals) if goals else pd.DataFrame()
        
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