"""
Pydantic v2 Contracts for Government Taxonomies (UNSPSC v26 and GeM).
"""

from typing import Optional
from pydantic import BaseModel, Field


class UNSPSCCommodity(BaseModel):
    code: str = Field(..., description="8-digit UNSPSC code")
    title: str = Field(..., description="Commodity or Category title")
    level: str = Field(..., description="Segment, Family, Class, or Commodity")
    parent_code: Optional[str] = Field(default=None, description="Parent taxonomy code or ROOT")


class GeMCategory(BaseModel):
    category_id: str = Field(..., description="GeM category identifier, e.g. GEM-FLANGE-WN")
    name: str = Field(..., description="Descriptive category title")
    parent_id: Optional[str] = Field(default=None, description="Parent GeM category identifier or ROOT")
