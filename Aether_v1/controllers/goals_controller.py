from datetime import date, datetime
from decimal import Decimal
from typing import Any

import altair as alt
import pandas as pd
from models.dates import Period, PeriodRange
from models.goals import Goal, GoalInfo, GoalProgressScore, GoalStatus, GoalType
from models.templates import Template, TemplateType
from services import (
    CategoryDBService,
    FinancialAnalysisService,
    GoalsDBService,
    PlottingService,
    TemplatesDBService,
    TransactionsDBService,
)

from .base_controller import BaseController


class GoalsController(BaseController):
    TEMPLATE_TYPE = TemplateType.GOAL

    def get_categories(self) -> list[str]:
        with self.quick_read_conn() as conn:
            categories_db = CategoryDBService(conn)

            return categories_db.get_categories_by_user(self.user_id)

    def get_category_id(self, category: str) -> int:
        with self.quick_read_conn() as conn:
            categories_db = CategoryDBService(conn)

            cat_id = categories_db.find_id(name=category)
            if cat_id is None:
                raise ValueError(f"Category {category} not found")
            return cat_id

    def get_category_by_id(self, category_id: int) -> str | None:
        with self.quick_read_conn() as conn:
            categories_db = CategoryDBService(conn)

            result = categories_db.find_by_id(category_id, columns=["name"])

            return result["name"] if result else None

    @staticmethod
    def get_goal_types() -> list[str]:
        return [goal_type.value for goal_type in GoalType]

    @staticmethod
    def get_period_ranges() -> list[str]:
        return [period_range.value for period_range in PeriodRange]

    @staticmethod
    def get_end_date(start_date: date, period_range: PeriodRange) -> date | None:
        return start_date + period_range.days_to_add if period_range.days_to_add else None

    def add_goal(self, new_goal: Goal) -> None:
        with self.session_conn() as conn:
            goals_db = GoalsDBService(conn)

            goals_db.add_goal(new_goal)

    def get_current_goals_names(self) -> list[str]:
        with self.quick_read_conn() as conn:
            goals_db = GoalsDBService(conn)

            return goals_db.get_unique_values("name", user_id=self.user_id)

    def get_current_goals(self) -> pd.DataFrame:
        with self.quick_read_conn() as conn:
            goals_db = GoalsDBService(conn)

            goals = goals_db.get_goals(
                user_id=self.user_id,
                status="current",
                columns=[
                    "name",
                    "type",
                    "amount",
                    "added_amount",
                    "start_date",
                    "end_date",
                    "status",
                ],
                order_by="start_date",
                order="asc",
                show_categories_names=True,
            )

            return pd.DataFrame(goals) if goals else pd.DataFrame()

    def get_past_goals(self) -> pd.DataFrame:
        with self.quick_read_conn() as conn:
            goals_db = GoalsDBService(conn)

            goals = goals_db.get_goals(
                user_id=self.user_id,
                status="past",
                columns=[
                    "name",
                    "type",
                    "amount",
                    "added_amount",
                    "start_date",
                    "end_date",
                    "status",
                ],
                order_by="end_date",
                order="desc",
                show_categories_names=True,
            )

            return pd.DataFrame(goals) if goals else pd.DataFrame()

    def update_goal_status(self, goal_dict: dict[str, Any], remaining: Decimal) -> GoalStatus:
        today = datetime.today()
        current_status = goal_dict["status"]

        if current_status == GoalStatus.ACTIVE:
            match goal_dict["type"]:
                case GoalType.SAVINGS:
                    if goal_dict["end_date"] < today and remaining > 0:
                        status = GoalStatus.FAILED
                    elif goal_dict["end_date"] > today and remaining <= 0:
                        status = GoalStatus.ACHIEVED
                    else:
                        return current_status
                case GoalType.BUDGET:
                    if goal_dict["end_date"] < today and remaining >= 0:
                        status = GoalStatus.ACHIEVED
                    elif goal_dict["end_date"] > today and remaining < 0:
                        status = GoalStatus.FAILED
                    else:
                        return current_status
                case GoalType.DEBT:
                    if goal_dict["end_date"] < today and remaining >= 0:
                        status = GoalStatus.ACHIEVED
                    elif goal_dict["end_date"] > today and remaining < 0:
                        status = GoalStatus.FAILED
                    else:
                        return current_status
                case GoalType.INVESTMENT:
                    if goal_dict["end_date"] < today and remaining > 0:
                        status = GoalStatus.FAILED
                    elif goal_dict["end_date"] > today and remaining <= 0:
                        status = GoalStatus.ACHIEVED
                    else:
                        return current_status
                case _:
                    return current_status

            with self.session_conn() as conn:
                goals_db = GoalsDBService(conn)

                goals_db.update(goal_dict["goal_id"], status=status)

                return status
        else:
            return current_status

    def get_goal_info(self, goal_name: str) -> GoalInfo:
        with self.quick_read_conn() as conn:
            goals_db = GoalsDBService(conn)

            goal_id = goals_db.find_id(name=goal_name, user_id=self.user_id)
            if goal_id is None:
                raise ValueError(f"Goal {goal_name} not found")

            goal_dict = goals_db.find_by_id(
                goal_id,
                columns=[
                    "goal_id",
                    "name",
                    "type",
                    "category_id",
                    "amount",
                    "added_amount",
                    "start_date",
                    "end_date",
                    "status",
                    "related_transaction_type",
                ],
            )

            if goal_dict is None:
                raise ValueError(f"Goal with id {goal_id} not found")

            transactions_db = TransactionsDBService(conn)

            current_amount = transactions_db.get_sum(
                "amount",
                start_date=goal_dict["start_date"],
                end_date=goal_dict["end_date"],
                user_id=self.user_id,
                category_id=goal_dict["category_id"],
                type=goal_dict["related_transaction_type"],
            )

            remaining = (goal_dict["amount"] + goal_dict["added_amount"]) - abs(current_amount)

            self.update_goal_status(goal_dict, remaining)

            category_name = self.get_category_by_id(goal_dict["category_id"])
            if category_name is None:
                category_name = "Unknown"

            current_amount_float = float(current_amount)
            remaining_float = float(remaining)

            return GoalInfo(
                goal_id=goal_dict["goal_id"],
                name=goal_dict["name"],
                type=GoalType(goal_dict["type"]),
                category_id=goal_dict["category_id"],
                category=category_name,
                amount=goal_dict["amount"],
                added_amount=goal_dict["added_amount"],
                start_date=goal_dict["start_date"],
                end_date=goal_dict["end_date"],
                status=GoalStatus(goal_dict["status"]),
                current_amount=current_amount_float,
                remaining=remaining_float,
                progress_porcentage=abs(current_amount_float)
                / float(goal_dict["amount"] + goal_dict["added_amount"]),
            )

    def add_amount(self, goal_id: int, amount: Decimal) -> None:
        with self.session_conn() as conn:
            goals_db = GoalsDBService(conn)

            goals_db.add_value("added_amount", amount, goal_id=goal_id)

    def get_donut_chart_goal_progress(self, goal_info: GoalInfo) -> Any:
        return PlottingService().donut_chart_goal_progress(goal_info)

    def get_goal_progress_score(self, goal_info: GoalInfo) -> GoalProgressScore:
        if goal_info.status == GoalStatus.ACHIEVED:
            return GoalProgressScore(score=1.0)
        elif goal_info.status == GoalStatus.FAILED:
            return GoalProgressScore(score=0.0)
        else:
            return FinancialAnalysisService.get_goal_progress_score(goal_info)

    def get_line_chart_goal_progress(self, goal_info: GoalInfo) -> alt.Chart | alt.LayerChart:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            transactions = transactions_db.get_transactions(
                user_id=self.user_id,
                period=Period(start_date=goal_info.start_date, end_date=goal_info.end_date),
                columns=["date", "amount"],
                category_id=goal_info.category_id,
                type=goal_info.type.transaction_type,
            )

            if transactions:
                dicts_list = []
                for t in transactions:
                    if isinstance(t, dict):
                        dicts_list.append(t)
                    else:
                        dicts_list.append(t.model_dump())

                df = pd.DataFrame(dicts_list)
                df["amount"] = df["amount"].abs()
                df["date"] = pd.to_datetime(df["date"])
                df.sort_values(by="date")

                df = df.groupby("date").agg({"amount": "sum"}).reset_index()
            else:
                df = pd.DataFrame({"date": [], "amount": []})

        plotting_service = PlottingService()

        trnsactions_line_chart = plotting_service.goal_transactions_line_chart(goal_info, df)
        target_progress_line_chart = plotting_service.goal_target_progress_line_chart(goal_info)
        target_amount_rule_chart = plotting_service.goal_target_amount_rule_chart(goal_info)

        return alt.layer(
            trnsactions_line_chart, target_progress_line_chart, target_amount_rule_chart
        )

    def get_goals_templates_names(self) -> dict[str, int]:
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
