from typing import List, Dict
from models.categories import NewCategory
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
    
    def get_categories_by_user_mapped(self, user_id: int) -> Dict[str, int]:
        categories = {}
        query = """
            SELECT name, category_id FROM categories WHERE user_id IS NULL OR user_id = %(user_id)s
        """
        
        result = self.execute_query(query, params={'user_id': user_id}, fetch= 'all', dict_cursor= True)
        
        for r in result:
            categories[r['name']] = r['category_id']
            
        return categories
    
    def _validate_new_category(self, user_id: int, new_category: NewCategory) -> False:
        query = f'''
            SELECT COUNT(*) FROM {self.table_name} WHERE {self.user_id} = %(user_id)s AND {self.name} = %(name)s AND "group" = %(group)s
        '''
        
        result = self.execute_query(query, params= {'user_id': user_id, 'name': new_category.name, 'group': new_category.group.value}, fetch= 'one')
        
        if result[0] > 0:
            return False
        else:
            return True
    
    def add_category(self, user_id: int, new_category: NewCategory) -> None:
        if not self._validate_new_category(user_id, new_category):
            raise ValueError('Category already exists')
        else:
            with self.transaction():
                query = f'''
                    INSERT INTO {self.table_name} ({self.user_id}, "group", {self.name}, {self.description})
                    VALUES (%(user_id)s, %(group)s, %(name)s, %(description)s)
                '''
                
                params = new_category.model_dump() | {'user_id': user_id}
                
                self.execute_query(query, params= params)