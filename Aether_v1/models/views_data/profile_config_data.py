from datetime import date

from pydantic import BaseModel

from ..users import UserProfile


class ProfileConfigViewData(BaseModel):
    """
    Data model for profile configuration view.
    Contains all the information needed to display the user profile page.
    """

    profile: UserProfile
    account_age_days: int
    account_age_formatted: str
    days_since_login: int
    transaction_count: int
    goal_count: int
    last_transaction_date: date | None = None
    days_since_last_transaction: int | None = None
