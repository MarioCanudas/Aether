from datetime import datetime, date
from functools import cached_property
from passlib.context import CryptContext
from typing import Optional
from services import UserDBService, TransactionsDBService, GoalsDBService
from models.users import UserUpdate, UserProfile
from models.views_data import ProfileConfigViewData
from .base_controller import BaseController

class ProfileConfigController(BaseController):
    @cached_property
    def password_context(self) -> CryptContext:
        return CryptContext(schemes= ['argon2'], deprecated= 'auto')
    
    def _hash_password(self, password: str) -> str:
        return self.password_context.hash(password)
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        return self.password_context.verify(password, hashed_password)
    
    def get_profile(self) -> UserProfile:
        with self.quick_read_conn() as conn:
            users_db = UserDBService(conn)
            
            return users_db.get_user(user_id= self.user_id)
    
    def _format_account_age(self, account_age_days: int) -> str:
        """
        Format account age in a human-readable format.
        
        Args:
            account_age_days: Number of days since account creation
            
        Returns:
            Formatted string representing account age
        """
        if account_age_days < 30:
            return f"{account_age_days} days"
        elif account_age_days < 365:
            months = account_age_days // 30
            return f"{months} month{'s' if months > 1 else ''}"
        else:
            years = account_age_days // 365
            remaining_months = (account_age_days % 365) // 30
            if remaining_months > 0:
                return f"{years} year{'s' if years > 1 else ''}, {remaining_months} month{'s' if remaining_months > 1 else ''}"
            else:
                return f"{years} year{'s' if years > 1 else ''}"
    
    async def get_profile_view_data(self) -> ProfileConfigViewData:
        """
        Gather all profile data asynchronously and return a ProfileConfigViewData model.
        
        Returns:
            ProfileConfigViewData containing all profile information and statistics
        """
        with self.quick_read_conn() as conn:
            users_db = UserDBService(conn)
            transactions_db = TransactionsDBService(conn)
            goals_db = GoalsDBService(conn)
            
            # Get profile data
            profile = users_db.get_user(user_id=self.user_id)
            
            # Calculate account age and days since last login
            today = date.today()
            account_age_days = (today - profile.created_at.date()).days
            days_since_login = (today - profile.last_login.date()).days
            
            # Get account statistics
            transaction_count = transactions_db.count(user_id=self.user_id)
            goal_count = goals_db.count(user_id=self.user_id)
            
            # Get last transaction date
            last_transaction_date: Optional[date] = None
            days_since_last_transaction: Optional[int] = None
            
            if transaction_count > 0:
                period = transactions_db.get_transactions_period(self.user_id)
                last_transaction_date = period.end_date
                days_since_last_transaction = (today - last_transaction_date).days
            
            # Format account age
            account_age_formatted = self._format_account_age(account_age_days)
            
            return ProfileConfigViewData(
                profile=profile,
                account_age_days=account_age_days,
                account_age_formatted=account_age_formatted,
                days_since_login=days_since_login,
                transaction_count=transaction_count,
                goal_count=goal_count,
                last_transaction_date=last_transaction_date,
                days_since_last_transaction=days_since_last_transaction
            )
        
    def modify_user(
            self, 
            current_password: str,
            new_username: Optional[str] = None, 
            new_password: Optional[str] = None
        ) -> None:
        profile = self.get_profile()
        
        if profile.username == new_username:
            raise ValueError('New username cannot be the same as the current username')
        
        with self.session_conn() as conn:
            users_db = UserDBService(conn)
            
            if not self._verify_password(current_password, profile.password_hash):
                raise ValueError('Invalid current password')
            
            new_password_hash = self._hash_password(new_password) if new_password else None
            
            user_id = users_db.find_id(username= profile.username)
            
            users_db.update_user(
                UserUpdate(
                    user_id= user_id, 
                    username= new_username, 
                    password_hash= new_password_hash,
                    updated_at= datetime.now()
                )
            )