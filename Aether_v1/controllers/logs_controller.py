from .base_controller import BaseController

class LogsController(BaseController):
    def update_user_id(self, user_id: int) -> None:
        self.user_session_service.set_current_user_by_id(user_id)
    
    def clear_user_session(self) -> None:
        self.user_session_service.clear_current_user()