"""Shapes of data for admin actions."""

from typing import Literal

from pydantic import BaseModel, Field


class MoneyIn(BaseModel):
    """Send (CREDIT) or take back (DEBIT) virtual money."""

    kind: Literal["CREDIT", "DEBIT"] = "CREDIT"
    amount: float = Field(gt=0, le=10000000)
    note: str = Field(default="", max_length=200)
    user_ids: list[int] = []  # pick students ...
    all_students: bool = False  # ... or everyone


class ActiveIn(BaseModel):
    is_active: bool
