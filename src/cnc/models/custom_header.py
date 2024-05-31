from typing import Optional, List

from .base_model import BaseModel


class CustomHeader(BaseModel):
    name: str
    value: str
    type: Optional[str] = "response"


class CustomHeaders(BaseModel):
    headers: List[CustomHeader] = []
    provider: str
