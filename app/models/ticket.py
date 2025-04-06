from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class TicketMessage:
    id: str
    ticket_id: str
    sender_id: str
    message: str
    created_at: Optional[datetime] = None
    sender: Optional[dict] = None

@dataclass
class Ticket:
    id: str
    subject: str
    status: str
    created_at: Optional[datetime] = None
    user_id: Optional[str] = None
    driver_id: Optional[str] = None
    order_id: Optional[str] = None
    description: str = ""
    user: Optional[dict] = None
    messages: List[TicketMessage] = field(default_factory=list)
    updates: List['TicketUpdate'] = field(default_factory=list)

@dataclass
class TicketUpdate:
    id: str
    ticket_id: str
    message: str
    created_at: datetime
    user_id: Optional[str] = None
    driver_id: Optional[str] = None