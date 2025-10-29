from typing import List
from services import CategoryDBService
from models.categories import NewCategory
from .base_controller import BaseController

class CategoriesConfigController(BaseController):
    def get_categories(self) -> List[str]:
        with self.quick_read_conn() as conn:
            categories_db = CategoryDBService(conn)
            
            return categories_db.get_categories_by_user(self.user_id)
        
    def add_category(self, new_category: NewCategory) -> None:
        with self.session_conn() as conn:
            categories_db = CategoryDBService(conn)
            
            categories_db.add_category(self.user_id, new_category)