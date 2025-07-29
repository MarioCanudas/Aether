from pydantic import BaseModel
from typing import List

class ColumnDelimitations(BaseModel):
    columns: List[str]
    x0: List[float]
    x1: List[float]