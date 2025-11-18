from typing import List, Optional, Dict
from services import CategoryDBService, TransactionsDBService, TemplatesDBService
from models.financial import TransactionRecord
from models.templates import Template, TemplateType
from .base_controller import BaseController

class AddTransactionController(BaseController):
    TEMPLATE_TYPE = TemplateType.TRANSACTION
    
    def get_categories(self) -> List[str]:
        with self.quick_read_conn() as conn:
            category_db = CategoryDBService(conn)
            
            return category_db.get_categories_by_user(self.user_id)
        
    def get_category_id(self, category: str) -> Optional[int]:
        with self.quick_read_conn() as conn:
            category_db = CategoryDBService(conn)
            
            return category_db.find_id(name= category)
        
    def get_category_name(self, category_id: int) -> str:
        with self.quick_read_conn() as conn:
            category_db = CategoryDBService(conn)
            
            result = category_db.find_by_id(category_id, columns= ['name'])
            
            return result['name']
        
    def add_transaction(self, transaction: TransactionRecord) -> None:
        with self.session_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions_db.add_records([transaction.model_dump()])
            
    def get_templates_names(self) -> Dict[str, int]:
        with self.quick_read_conn() as conn:
            transactions_templates_db = TemplatesDBService(conn)
            
            return transactions_templates_db.get_templates_names(self.user_id, self.TEMPLATE_TYPE)
        
    def get_template(self, template_id: int) -> Template | None:
        with self.quick_read_conn() as conn:
            transactions_templates_db = TemplatesDBService(conn)
            
            return transactions_templates_db.get_template(template_id)
        
    def add_template(self, template: Template) -> None:
        with self.session_conn() as conn:
            transactions_templates_db = TemplatesDBService(conn)
            
            transactions_templates_db.add_template(template)
        
    def update_template(self, template_id: int, updated_template: Template) -> None:
        with self.session_conn() as conn:
            transactions_templates_db = TemplatesDBService(conn)
            
            transactions_templates_db.update_template(template_id, updated_template)
            
    def delete_template(self, template_id: int) -> None:
        with self.session_conn() as conn:
            transactions_templates_db = TemplatesDBService(conn)
            
            transactions_templates_db.delete_template(template_id)
        