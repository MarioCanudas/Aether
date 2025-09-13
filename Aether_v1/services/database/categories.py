from typing import List
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
    
    def get_categories_by_user(self, user_id: int) -> List[str]:
        query = """
            SELECT name FROM categories WHERE user_id IS NULL OR user_id = %(user_id)s
        """
        
        result = self.execute_query(query, params={'user_id': user_id}, fetch= 'all')
        
        return [r[0] for r in result]