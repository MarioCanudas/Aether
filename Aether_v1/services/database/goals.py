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