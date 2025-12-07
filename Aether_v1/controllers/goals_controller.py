import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
import altair as alt
from decimal import Decimal
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from services import (CategoryDBService, GoalsDBService, TransactionsDBService, PlottingService, 
                      FinancialAnalysisService, TemplatesDBService)
from models.dates import PeriodRange
from models.goals import Goal, GoalInfo, GoalStatus, GoalType, GoalProgressScore
from models.templates import Template, TemplateType
from .base_controller import BaseController

class GoalsController(BaseController):
    TEMPLATE_TYPE = TemplateType.GOAL
    
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
    def get_end_date(start_date: date, period_range: PeriodRange) -> Optional[date]:
        return start_date + period_range.days_to_add if period_range.days_to_add else None
    
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
        
    def update_goal_status(self, goal_dict: Dict[str, Any], remaining: Decimal) -> GoalStatus:
        today = datetime.today()
        current_status = goal_dict['status']
        
        if current_status == GoalStatus.ACTIVE:
            match goal_dict['type']:
                case GoalType.SAVINGS:
                    if goal_dict['end_date'] < today and remaining > 0:
                        status = GoalStatus.FAILED
                    elif goal_dict['end_date'] > today and remaining <= 0:
                        status = GoalStatus.ACHIEVED
                    else:
                        return current_status
                case GoalType.BUDGET:
                    if goal_dict['end_date'] < today and remaining >= 0:
                        status = GoalStatus.ACHIEVED
                    elif goal_dict['end_date'] > today and remaining < 0:
                        status = GoalStatus.FAILED
                    else:
                        return current_status
                case GoalType.DEBT:
                    if goal_dict['end_date'] < today and remaining >= 0:
                        status = GoalStatus.ACHIEVED
                    elif goal_dict['end_date'] > today and remaining < 0:
                        status = GoalStatus.FAILED
                    else:
                        return current_status
                case GoalType.INVESTMENT:
                    if goal_dict['end_date'] < today and remaining > 0:
                        status = GoalStatus.FAILED
                    elif goal_dict['end_date'] > today and remaining <= 0:
                        status = GoalStatus.ACHIEVED
                    else:
                        return current_status
                case _:
                    return current_status
                
            with self.session_conn() as conn:
                goals_db = GoalsDBService(conn)
                
                goals_db.update(goal_dict['goal_id'], status= status)
                
                return status
        else:
            return current_status
        
    def get_goal_info(self, goal_name: str) -> GoalInfo:
        with self.quick_read_conn() as conn:
            goals_db = GoalsDBService(conn)
            
            goal_id = goals_db.find_id(name= goal_name, user_id= self.user_id)
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
            
            status = self.update_goal_status(goal_dict, remaining)
            
            return GoalInfo(
                goal_id= goal_dict['goal_id'],
                name= goal_dict['name'],
                type= GoalType(goal_dict['type']),
                category_id= goal_dict['category_id'],
                category= self.get_category_by_id(goal_dict['category_id']),
                amount= goal_dict['amount'],
                added_amount= goal_dict['added_amount'],
                start_date= goal_dict['start_date'],
                end_date= goal_dict['end_date'],
                status= status,    
                current_amount= current_amount,
                remaining= remaining,
                progress_porcentage= abs(current_amount) / (goal_dict['amount'] + goal_dict['added_amount'])
            )
        
    def add_amount(self, goal_id: int, amount: Decimal) -> None:
        with self.session_conn() as conn:
            goals_db = GoalsDBService(conn)
            
            goals_db.add_value('added_amount', amount, goal_id= goal_id)
            
    def get_donut_chart_goal_progress(self, goal_info: GoalInfo) -> plt.figure:
        return PlottingService().donut_chart_goal_progress(goal_info)
    
    def get_goal_progress_score(self, goal_info: GoalInfo) -> GoalProgressScore:
        if goal_info.status == GoalStatus.ACHIEVED:
            return GoalProgressScore(score= 1.0)
        elif goal_info.status == GoalStatus.FAILED:
            return GoalProgressScore(score= 0.0)
        else:
            return FinancialAnalysisService.get_goal_progress_score(goal_info)
    
    def get_line_chart_goal_progress(self, goal_info: GoalInfo) -> alt.Chart:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions = transactions_db.get_transactions(
                user_id= self.user_id,
                period= (goal_info.start_date, goal_info.end_date),
                columns= ['date', 'amount'],
                category_id= goal_info.category_id,
                type= goal_info.type.transaction_type
            )
            
            if transactions:
                df = pd.DataFrame([t.model_dump() for t in transactions])
                df['amount'] = df['amount'].abs()
                df['date'] = pd.to_datetime(df['date'])
                df.sort_values(by= 'date')

                df = df.groupby('date').agg({'amount': 'sum'}).reset_index()
            else:
                df = pd.DataFrame(columns= ['date', 'amount'])
                
        plotting_service = PlottingService()
            
        trnsactions_line_chart = plotting_service.goal_transactions_line_chart(goal_info, df)
        target_progress_line_chart = plotting_service.goal_target_progress_line_chart(goal_info)
        target_amount_rule_chart = plotting_service.goal_target_amount_rule_chart(goal_info)
        
        return alt.layer(trnsactions_line_chart, target_progress_line_chart, target_amount_rule_chart)
    
    def get_goals_templates_names(self) -> Dict[str, int]:
        with self.quick_read_conn() as conn:
            goals_templates_db = TemplatesDBService(conn)
            
            return goals_templates_db.get_templates_names(self.user_id, self.TEMPLATE_TYPE)
        
    def get_goal_template(self, template_id: int) -> Template | None:
        with self.quick_read_conn() as conn:
            goals_templates_db = TemplatesDBService(conn)
            
            return goals_templates_db.get_template(template_id)
        
    def add_goal_template(self, new_template: Template) -> None:
        with self.session_conn() as conn:
            goals_templates_db = TemplatesDBService(conn)
            
            goals_templates_db.add_template(new_template)
        
    def update_goal_template(self, template_id: int, updated_template: Template) -> None:
        with self.session_conn() as conn:
            goals_templates_db = TemplatesDBService(conn)
            
            goals_templates_db.update_template(template_id, updated_template)
            
    def delete_goal_template(self, template_id: int) -> None:
        with self.session_conn() as conn:
            goals_templates_db = TemplatesDBService(conn)
            
            goals_templates_db.delete_template(template_id)