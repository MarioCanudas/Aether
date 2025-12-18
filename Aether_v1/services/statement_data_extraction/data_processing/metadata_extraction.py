import re
from datetime import date
from decimal import Decimal
from functools import cache
from typing import Literal

import pandas as pd
from dateutil.relativedelta import relativedelta
from models.amounts import TransactionType
from models.bank_properties import Balances, Metadata, StatementType
from models.dates import Period
from models.transactions import Transaction
from utils import clean_amount, search_phrase_in_df, to_decimal

from ..core import MetadataExtractor


class DefaultMetadataExtractor(MetadataExtractor):
    @cache
    def get_period_idx(self) -> int | None:
        """
        Finds the index position where the statement period information starts.
        Searches for a specific phrase and returns the index after the match.
        """
        df_extracted_words = self.corrected_extracted_words.df.copy()
        period_phrase = self.bank_properties.period_phrase

        if not period_phrase or df_extracted_words.empty:
            return None

        # Convert period_phrase to lowercase once for efficient comparison
        period_phrase_lower = [phrase.lower() for phrase in period_phrase]

        # Search for the period phrase in the extracted words
        for i in range(len(df_extracted_words) - len(period_phrase)):
            window_words = df_extracted_words["text"].iloc[i : i + len(period_phrase)]
            processed_window = [word.lower().rstrip(":") for word in window_words]

            if processed_window == period_phrase_lower:
                return i + len(period_phrase)  # First word after match

        raise ValueError(f"Period phrase '{period_phrase}' not found in the extracted words.")

    @cache
    def get_period(self) -> Period | None:
        """"""
        period_idx = self.get_period_idx()

        if period_idx is None:
            raise ValueError("Period phrase not found in the extracted words.")

        search_window: pd.DataFrame = self.corrected_extracted_words.df.iloc[
            period_idx : period_idx + 20
        ]
        texts: list[str] = search_window["text"].tolist()

        period_pattern: str | None = self.bank_properties.period_pattern

        if not period_pattern:
            return None

        pattern_parts: list[str] = period_pattern.split(" ")
        n_parts: int = len(pattern_parts)

        found_dates = []
        for i in range(len(texts) - n_parts):
            candidate = " ".join(texts[i : i + n_parts]) if n_parts > 1 else texts[i]
            date_match = re.match(period_pattern, candidate)

            if date_match:
                found_dates.append(date_match)

            if len(found_dates) == 2:
                break

        if not found_dates:
            return None

        period_dates = []
        for date_match in found_dates:
            # Convert month to number if needed
            month_pattern: dict[str, str] | None = self.bank_properties.period_month_pattern
            if self.bank_properties.period_group is None:
                raise ValueError("Period group configuration is missing")

            year_group: int | None = self.bank_properties.period_group.year
            month_group: int = self.bank_properties.period_group.month
            day_group: int = self.bank_properties.period_group.day

            # Year can be None in DateGroups, but should be present here if pattern expects it
            year: str = (
                date_match.group(year_group) if year_group is not None else str(date.today().year)
            )  # Fallback if None?
            month: str = date_match.group(month_group)
            day: str = date_match.group(day_group)

            # Validate date values
            if len(year) == 2:
                year = "20" + year

            if month_pattern is not None and month in month_pattern.keys():
                month = month_pattern[month]

            if not day.isdigit():
                raise ValueError(f"Invalid day format: {day}")

            date_period = date(int(year), int(month), int(day))
            period_dates.append(date_period)

        period_dates = list(set(period_dates))

        if len(period_dates) == 0:
            raise ValueError("No period dates found in the statement.")
        elif len(period_dates) == 1:
            previous_date = period_dates[0] - relativedelta(months=1) + relativedelta(days=1)
            return Period(start_date=previous_date, end_date=period_dates[0])
        elif len(period_dates) == 2:
            period = sorted(period_dates)
            return Period(start_date=period[0], end_date=period[1])
        else:
            raise ValueError("More than 2 period dates found in the statement.")

    def get_generated_amount(self) -> Decimal | None:
        """
        Get the generated amount from the statement text.
        Searches for the generated amount phrase and returns the following numeric value.
        """
        if self.bank_properties.statement_type == StatementType.CREDIT:
            return None

        df_extracted_words = self.corrected_extracted_words.df.copy()

        generated_amount_phrase = self.bank_properties.generated_amount_phrase

        if not generated_amount_phrase or df_extracted_words.empty:
            return None

        phrase_idx = search_phrase_in_df(df_extracted_words, generated_amount_phrase)

        if phrase_idx is None:
            return None

        search_window: pd.DataFrame = df_extracted_words.iloc[
            phrase_idx + len(generated_amount_phrase) : phrase_idx + 15
        ]
        texts: list[str] = search_window["text"].tolist()

        for text in texts:
            text = clean_amount(text)

            try:
                amount = to_decimal(text)

                if amount > Decimal("0.00"):
                    return amount
            except ValueError:
                continue
        else:
            return None

    def get_generated_amount_row(self, user_id: int, filename: str) -> Transaction | None:
        generated_amount = self.get_generated_amount()

        if generated_amount is None:
            return None

        period = self.get_period()
        if period is None:
            raise ValueError("Period could not be determined")

        final_date = pd.to_datetime(period.end_date)

        return Transaction(
            user_id=user_id,
            date=final_date,
            description="Intereses generados",
            amount=generated_amount,
            type=TransactionType.INCOME,
            bank=self.bank_properties.bank,
            statement_type=self.bank_properties.statement_type,
            filename=filename,
        )

    def get_balance(self, balance: Literal["initial", "final"]) -> float | None:
        """
        Extracts the initial balance amount from the statement text.
        Searches for the initial balance phrase and returns the following numeric value.
        """
        if self.bank_properties.statement_type == StatementType.CREDIT:
            return None

        df_extracted_words = self.corrected_extracted_words.df.copy()

        if balance == "initial":
            balance_phrase = self.bank_properties.initial_balance_phrase
        elif balance == "final":
            balance_phrase = self.bank_properties.final_balance_phrase
        else:
            raise ValueError(f"Invalid balance type: {balance}")

        if not balance_phrase or df_extracted_words.empty:
            return None

        # Search for initial balance phrase and extract the amount that follows
        for i in range(len(df_extracted_words) - len(balance_phrase)):
            window_words = df_extracted_words["text"].iloc[i : i + len(balance_phrase)]
            processed_window = [word.lower().rstrip(":") for word in window_words]

            if processed_window == balance_phrase:
                balance_val = df_extracted_words["text"].iloc[i + len(balance_phrase)]
                balance_val = clean_amount(balance_val)

                try:
                    return float(balance_val)
                except ValueError:
                    return None

        return None

    def get_initial_balance_row(self, user_id: int, filename: str) -> Transaction | None:
        initial_balance = self.get_balance("initial")

        if initial_balance is None:
            return None

        period = self.get_period()
        if period is None:
            raise ValueError("Period could not be determined")

        first_date = pd.to_datetime(period.start_date)

        return Transaction(
            user_id=user_id,
            date=first_date,
            description="Saldo inicial",
            amount=to_decimal(initial_balance),
            type=TransactionType.INITIAL_BALANCE,
            bank=self.bank_properties.bank,
            statement_type=self.bank_properties.statement_type,
            filename=filename,
        )

    def get_years(self) -> list[int]:
        """ """
        period: Period | None = self.get_period()

        if not period:
            period_idx = self.get_period_idx()

            df_extracted_words = self.corrected_extracted_words.df.copy()
            period_pattern = self.bank_properties.period_pattern
            if self.bank_properties.period_group is None:
                raise ValueError("Period group configuration is missing")
            year_group = self.bank_properties.period_group.year
            detected_years = []

            if period_idx is None or df_extracted_words.empty:
                return detected_years

            # Search for years in the period section (limited window after period phrase)
            period_values = df_extracted_words.iloc[period_idx : period_idx + 15]

            for text in period_values["text"]:
                # Use custom pattern if available, otherwise fallback to generic year pattern
                if period_pattern:
                    year_match = re.search(period_pattern, text)

                    if year_match and year_group is not None:
                        try:
                            year = int(year_match.group(year_group))
                            detected_years.append(year)
                        except (ValueError, IndexError):
                            continue

                else:
                    year_match = re.search(r"\b20\d{2}\b", text)

                    if year_match:
                        try:
                            year = int(year_match.group())
                            detected_years.append(year)
                        except ValueError:
                            continue

            return sorted(list(set(detected_years)))

        else:
            years = [period.start_date.year, period.end_date.year]
            years = list(set(years))

            return sorted(years)

    def get_months(self) -> list[str]:
        """
        Extracts the months from the statement text.
        """
        period: Period | None = self.get_period()

        if not period:
            return []

        months = [period.start_date.month, period.end_date.month]
        months = list(set(months))

        return sorted([str(m) for m in months])

    def get_metadata(self) -> Metadata:
        bank = self.bank_properties.bank
        statement_type = self.bank_properties.statement_type
        period = self.get_period()
        if period is None:
            raise ValueError("Period is missing for metadata")

        initial_balance = self.get_balance("initial")
        final_balance = self.get_balance("final")

        balances = Balances(initial=initial_balance, final=final_balance)

        return Metadata(bank=bank, statement_type=statement_type, period=period, balances=balances)
