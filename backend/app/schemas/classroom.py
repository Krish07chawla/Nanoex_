"""Shapes of data for live classes."""

from typing import Literal

from pydantic import BaseModel, Field


class ClassIn(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    symbols: list[str] = Field(min_length=1, max_length=6)


class JoinIn(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class NoteIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    symbol: str | None = None
    kind: Literal["NOTE", "BUY_IDEA", "SELL_IDEA"] = "NOTE"


class TextIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
