import pandas as pd
import matplotlib.pyplot as plt
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import List, Optional
from services import CategoryDBService, GoalsDBService, TransactionsDBService, PlottingService
from models.dates import PeriodRange
from models.goals import Goal, GoalInfo, GoalStatus, GoalType
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
        
    def get_category_by_id(self, category_id: int) -> str | None:
        with self.quick_read_conn() as conn:
            categories_db = CategoryDBService(conn)
            
            result =  categories_db.find_by_id(category_id, columns= ['name'])
            
            return result['name'] if result else None
        
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
                columns= ['name', 'type', 'amount', 'added_amount', 'start_date', 'end_date', 'status'],
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
                columns= ['name', 'type', 'amount', 'added_amount', 'start_date', 'end_date', 'status'],
                order_by= 'end_date',
                order= 'desc',
                show_categories_names= True
            )
            
            return pd.DataFrame(goals) if goals else pd.DataFrame()
        
    def get_goal_info(self, goal_name: str) -> GoalInfo:
        with self.quick_read_conn() as conn:
            goals_db = GoalsDBService(conn)
            
            goal_id = goals_db.find_id(name= goal_name)
            goal_dict = goals_db.find_by_id(
                goal_id, 
                columns= ['goal_id', 'name', 'type', 'category_id', 'amount', 'added_amount', 'start_date', 
                          'end_date', 'status', 'related_transaction_type']
            )
            
            transactions_db = TransactionsDBService(conn)
            
            current_amount = transactions_db.get_sum(
                'amount',
                start_date= goal_dict['start_date'],
                end_date= goal_dict['end_date'],
                user_id= self.user_id,
                category_id= goal_dict['category_id'],
                type= goal_dict['related_transaction_type']
            )
            
            remaining = (goal_dict['amount'] + goal_dict['added_amount']) - abs(current_amount) 
            
            return GoalInfo(
                goal_id= goal_dict['goal_id'],
                name= goal_dict['name'],
                type= GoalType(goal_dict['type']),
                category= self.get_category_by_id(goal_dict['category_id']),
                amount= goal_dict['amount'],
                added_amount= goal_dict['added_amount'],
                start_date= goal_dict['start_date'],
                end_date= goal_dict['end_date'],
                status= GoalStatus(goal_dict['status']),    
                current_amount= current_amount,
                remaining= remaining,
                progress_porcentage= abs(current_amount) / goal_dict['amount']
            )
        
    def add_amount(self, goal_id: int, amount: Decimal) -> None:
        with self.session_conn() as conn:
            goals_db = GoalsDBService(conn)
            
            goals_db.update(goal_id, added_amount= amount)
            
    def get_donut_chart_goal_progress(self, goal_info: GoalInfo) -> plt.figure:
        return PlottingService().donut_chart_goal_progress(goal_info)