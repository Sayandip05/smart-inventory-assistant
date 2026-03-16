"""
Inventory repository — data access layer.

All raw database queries for locations, items, and transactions live here.
Services call the repository; the repository talks to SQLAlchemy.
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional, List

from app.database.models import Location, Item, InventoryTransaction

logger = logging.getLogger("smart_inventory.repo.inventory")


class InventoryRepository:
    """Encapsulates all inventory-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    # ── Locations ──

    def get_all_locations(self) -> List[Location]:
        return self.db.query(Location).all()

    def get_location_by_id(self, location_id: int) -> Optional[Location]:
        return self.db.query(Location).filter(Location.id == location_id).first()

    def get_location_by_name(self, name: str) -> Optional[Location]:
        return self.db.query(Location).filter(Location.name == name).first()

    def create_location(self, **kwargs) -> Location:
        location = Location(**kwargs)
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    # ── Items ──

    def get_all_items(self) -> List[Item]:
        return self.db.query(Item).all()

    def get_item_by_id(self, item_id: int) -> Optional[Item]:
        return self.db.query(Item).filter(Item.id == item_id).first()

    def get_item_by_name(self, name: str) -> Optional[Item]:
        return self.db.query(Item).filter(Item.name == name).first()

    def create_item(self, **kwargs) -> Item:
        item = Item(**kwargs)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    # ── Transactions ──

    def get_previous_transaction(
        self, location_id: int, item_id: int, before_date: date
    ) -> Optional[InventoryTransaction]:
        """Get the most recent transaction before a given date."""
        return (
            self.db.query(InventoryTransaction)
            .filter(
                InventoryTransaction.location_id == location_id,
                InventoryTransaction.item_id == item_id,
                InventoryTransaction.date < before_date,
            )
            .order_by(InventoryTransaction.date.desc())
            .first()
        )

    def get_latest_transaction(
        self, location_id: int, item_id: int
    ) -> Optional[InventoryTransaction]:
        """Get the most recent transaction for a location/item pair."""
        return (
            self.db.query(InventoryTransaction)
            .filter(
                InventoryTransaction.location_id == location_id,
                InventoryTransaction.item_id == item_id,
            )
            .order_by(InventoryTransaction.date.desc())
            .first()
        )

    def create_transaction(self, **kwargs) -> InventoryTransaction:
        tx = InventoryTransaction(**kwargs)
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    # ── Bulk / Reset ──

    def count_transactions(self) -> int:
        return self.db.query(InventoryTransaction).count()

    def count_items(self) -> int:
        return self.db.query(Item).count()

    def count_locations(self) -> int:
        return self.db.query(Location).count()

    def delete_all_transactions(self) -> int:
        return self.db.query(InventoryTransaction).delete()

    def delete_all_items(self) -> int:
        return self.db.query(Item).delete()

    def delete_all_locations(self) -> int:
        return self.db.query(Location).delete()

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()
