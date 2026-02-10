from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)
    region = Column(String(100), nullable=False)
    address = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    transactions = relationship("InventoryTransaction", back_populates="location")

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    unit = Column(String(50), nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    min_stock = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    transactions = relationship("InventoryTransaction", back_populates="item")

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    date = Column(Date, nullable=False)
    opening_stock = Column(Integer, nullable=False)
    received = Column(Integer, nullable=False, default=0)
    issued = Column(Integer, nullable=False, default=0)
    closing_stock = Column(Integer, nullable=False)
    notes = Column(Text)
    entered_by = Column(String(100), default="system")
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    location = relationship("Location", back_populates="transactions")
    item = relationship("Item", back_populates="transactions")