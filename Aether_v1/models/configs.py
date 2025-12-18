from pydantic import BaseModel


class DonutChartConfig(BaseModel):
    completion_percentage: int
    label: str
    color: str
    points: str
