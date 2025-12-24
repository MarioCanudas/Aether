from decimal import Decimal

import altair as alt
from pydantic import BaseModel, ConfigDict, field_validator

from ..dates import Period
from .all_views import PeriodsOptions


class AnalysisAmountsPerPeriod(BaseModel):
    current_month: Decimal | int
    last_month: Decimal | int
    avarage: Decimal | int
    all_time: Decimal | int

    def __getitem__(self, key: PeriodsOptions) -> Decimal | int | None:
        match key:
            case PeriodsOptions.ALL_TIME:
                return self.all_time
            case PeriodsOptions.CURRENT_MONTH:
                return self.current_month
            case PeriodsOptions.LAST_MONTH:
                return self.last_month
            case PeriodsOptions.AVARAGE:
                return self.avarage
            case _:
                raise ValueError(f"Invalid period option: {key}")


class AnalysisAmounts(BaseModel):
    accumulated_amount: Decimal | AnalysisAmountsPerPeriod
    max_amount: Decimal | AnalysisAmountsPerPeriod
    frecuency: int | AnalysisAmountsPerPeriod

    @property
    def values(self) -> list[Decimal | AnalysisAmountsPerPeriod | int]:
        return [self.accumulated_amount, self.max_amount, self.frecuency]

    def _validate_amounts_per_period(self) -> bool:
        for value in self.values:
            if isinstance(value, (Decimal, int)):
                return False
        else:
            return True

    def __getitem__(self, key: PeriodsOptions) -> "AnalysisAmounts":
        if not self._validate_amounts_per_period():
            raise ValueError(
                "Accumulated amount, max amount and frecuency must be AnalysisAmountsPerPeriod"
            )

        acc_amount = self.accumulated_amount
        max_amount = self.max_amount
        frec_amount = self.frecuency

        if not isinstance(acc_amount, AnalysisAmountsPerPeriod):
            raise ValueError("accumulated_amount is not of type AnalysisAmountsPerPeriod")
        if not isinstance(max_amount, AnalysisAmountsPerPeriod):
            raise ValueError("max_amount is not of type AnalysisAmountsPerPeriod")
        if not isinstance(frec_amount, AnalysisAmountsPerPeriod):
            raise ValueError("frecuency is not of type AnalysisAmountsPerPeriod")

        match key:
            case PeriodsOptions.ALL_TIME:
                return AnalysisAmounts(
                    accumulated_amount=Decimal(acc_amount.all_time),
                    max_amount=Decimal(max_amount.all_time),
                    frecuency=int(frec_amount.all_time),
                )
            case PeriodsOptions.CURRENT_MONTH:
                return AnalysisAmounts(
                    accumulated_amount=Decimal(acc_amount.current_month),
                    max_amount=Decimal(max_amount.current_month),
                    frecuency=int(frec_amount.current_month),
                )
            case PeriodsOptions.LAST_MONTH:
                return AnalysisAmounts(
                    accumulated_amount=Decimal(acc_amount.last_month),
                    max_amount=Decimal(max_amount.last_month),
                    frecuency=int(frec_amount.last_month),
                )
            case PeriodsOptions.AVARAGE:
                return AnalysisAmounts(
                    accumulated_amount=Decimal(acc_amount.avarage),
                    max_amount=Decimal(max_amount.avarage),
                    frecuency=int(frec_amount.avarage),
                )
            case _:
                raise ValueError(f"Invalid period option: {key}")


class AnalysisViewData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    period: Period
    amount_per_category_chart: alt.Chart | alt.LayerChart | None
    avg_monthly_bar_chart: alt.Chart | None
    avg_daily_bar_chart: alt.Chart | None
    analysis_amounts: AnalysisAmounts

    @field_validator("amount_per_category_chart")
    @classmethod
    def validate_amount_per_category_chart(
        cls, amount_per_category_chart: alt.Chart | alt.LayerChart | None
    ) -> alt.Chart | alt.LayerChart | None:
        if (amount_per_category_chart is not None) and not isinstance(
            amount_per_category_chart, (alt.Chart, alt.LayerChart)
        ):
            raise ValueError("Amount per category chart must be a Altair Chart object")

        return amount_per_category_chart

    @field_validator("avg_monthly_bar_chart")
    @classmethod
    def validate_avg_monthly_bar_chart(
        cls, avg_monthly_bar_chart: alt.Chart | None
    ) -> alt.Chart | None:
        if (avg_monthly_bar_chart is not None) and not isinstance(avg_monthly_bar_chart, alt.Chart):
            raise ValueError("Average monthly bar chart must be a Altair Chart object")

        return avg_monthly_bar_chart

    @field_validator("avg_daily_bar_chart")
    @classmethod
    def validate_avg_daily_bar_chart(
        cls, avg_daily_bar_chart: alt.Chart | None
    ) -> alt.Chart | None:
        if (avg_daily_bar_chart is not None) and not isinstance(avg_daily_bar_chart, alt.Chart):
            raise ValueError("Average daily bar chart must be a Altair Chart object")

        return avg_daily_bar_chart
