from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Dict
from decimal import Decimal

@dataclass
class Order:
    id: str
    user_id: str
    pickup_location: str
    delivery_location: str
    item_description: str
    weight: Optional[float] = None
    price: Optional[float] = None
    status: str = 'pending'
    driver_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: datetime = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    user: Optional[Dict] = None  # For joined user data
    driver: Optional[Dict] = None  # For joined driver data

@dataclass
class OrderAssignment:
    id: str
    order_id: str
    driver_id: str
    status: str = 'pending'
    expected_delivery_date: Optional[date] = None
    created_at: Optional[datetime] = None

@dataclass
class OrderUpdate:
    id: str
    order_id: str
    driver_id: str
    status: str
    update_message: str
    created_at: datetime = None 