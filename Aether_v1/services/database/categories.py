from .base_db import BaseDBService

class CategoryDBService(BaseDBService):
    # Table information
    table_name = 'categories'
    allowed_columns = {'category_id', 'user_id', 'group', 'name', 'description'}
    
    # Column names
    id_col = 'category_id'
    user_id = 'user_id'
    group = 'group'
    name = 'name'
    description = 'description'