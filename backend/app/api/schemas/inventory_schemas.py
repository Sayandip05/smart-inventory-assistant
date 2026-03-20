from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class TransactionItem(BaseModel):
    item_id: int
    received: int = Field(ge=0, description="Quantity received (must be >= 0)")
    issued: int = Field(ge=0, description="Quantity issued/used (must be >= 0)")
    notes: Optional[str] = None


class SingleTransactionRequest(BaseModel):
    location_id: int
    item_id: int
    date: date
    received: int = Field(ge=0)
    issued: int = Field(ge=0)
    notes: Optional[str] = None
    entered_by: Optional[str] = "staff"


class BulkTransactionRequest(BaseModel):
    location_id: int
    date: date
    items: List[TransactionItem]
    entered_by: Optional[str] = "staff"


class CreateLocationRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    type: str = Field(min_length=2, max_length=50)
    region: str = Field(min_length=2, max_length=100)
    address: Optional[str] = None


class CreateItemRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=2, max_length=100)
    unit: str = Field(min_length=1, max_length=50)
    lead_time_days: int = Field(ge=1, le=365)
    min_stock: int = Field(ge=0)


class ResetDataRequest(BaseModel):
    confirm: bool = False
