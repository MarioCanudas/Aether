import asyncio
from datetime import date
from typing import Any

import pandas as pd
from altair import Chart
from dateutil.relativedelta import relativedelta
from models.amounts import TransactionType
from models.bank_properties import BankName, StatementType
from models.cards import Card, CardMetrics
from models.transactions import Transaction
from models.views_data import CardViewData
from services import CardsDBService, PlottingService, TransactionsDBService
from utils import months_map

from .base_controller import BaseController


class CardsViewController(BaseController):
    def add_card(
        self,
        card_name: str,
        card_bank: BankName,
        statement_type: StatementType,
        expiration_date: date | None = None,
    ) -> None:
        card = Card(
            user_id=self.user_id,
            card_name=card_name,
            card_bank=card_bank,
            statement_type=statement_type,
            expiration_date=expiration_date,
        )

        with self.session_conn() as conn:
            cards_db = CardsDBService(conn)

            cards_db.add_card(card)

    def get_cards(self, only_name: bool = False) -> list[Card] | list[str]:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)

            cards = cards_db.get_cards(self.user_id)

        if only_name:
            return [card.card_name for card in cards]
        else:
            return cards

    def get_card_by_name(self, card_name: str) -> Card:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)

            card_id = cards_db.find_id(card_name=card_name, user_id=self.user_id)
            if card_id is None:
                raise ValueError(f"Card {card_name} not found")

            card = cards_db.get_card_by_id(self.user_id, card_id)
            if card is None:
                raise ValueError(f"Card with id {card_id} not found")
            return card

    async def get_income_vs_expenses_chart(
        self, transactions: list[dict[str, Any]] | list[Transaction]
    ) -> Chart | None:
        if not transactions:
            return None

        # Ensure we work with dicts
        dicts_list: list[dict[str, Any]] = []
        for t in transactions:
            if isinstance(t, Transaction):
                dicts_list.append(t.model_dump())
            else:
                dicts_list.append(t)

        today = date.today()
        start_date = today - relativedelta(months=6)
        end_date = today

        df = pd.DataFrame(dicts_list)
        df["date"] = pd.to_datetime(df["date"])

        filtered_df = df[df["date"].between(pd.to_datetime(start_date), pd.to_datetime(end_date))]
        filtered_df = self.generics_validator.validate_dataframe(filtered_df)

        filtered_df["month"] = filtered_df["date"].month
        filtered_df["month-year"] = filtered_df["date"].strftime("%Y-%m")
        filtered_df["month_label"] = filtered_df["month"].apply(lambda x: months_map(x))

        grouped = filtered_df.groupby(["month-year", "type"], as_index=False).agg(
            amount=("amount", "sum"),
            month_label=("month_label", "first"),
            month=("month", "first"),
        )

        grouped = self.generics_validator.validate_dataframe(grouped)

        # Fix assignment to new column or slice
        grouped["amount"] = grouped["amount"].apply(lambda x: abs(x))
        grouped["amount"] = grouped["amount"].astype("float64")

        plotting_service = PlottingService()

        async with asyncio.TaskGroup() as tg:
            income_vs_expenses_chart = tg.create_task(
                plotting_service.get_income_vs_expenses_bar_chart(grouped)
            )

        return income_vs_expenses_chart.result()

    async def get_card_view_data(self, card_id: int) -> CardViewData:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            income = transactions_db.get_sum(
                column="amount", card_id=card_id, type=TransactionType.INCOME
            )
            expenses = transactions_db.get_sum(
                column="amount", card_id=card_id, type=TransactionType.EXPENSE
            )
            balance = income - expenses

            metrics = CardMetrics(
                total_income=income, total_expenses=expenses, total_balance=balance
            )

            transactions = transactions_db.get_transactions(
                user_id=self.user_id,
                show_categories_names=True,
                card_id=card_id,
                order_col="date",
                order="desc",
                limit=5,
                transaction_model=False,
            )

            transactions = await self.generics_validator.validate_list_of_dicts(transactions)

            return CardViewData(
                metrics=metrics,
                transactions=transactions,
                income_vs_expenses_chart=await self.get_income_vs_expenses_chart(transactions),
            )
