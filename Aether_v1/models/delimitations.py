from pydantic import BaseModel

class ColumnDelimitations(BaseModel):
    columns: list[str]
    x0: list[float]
    x1: list[float]
