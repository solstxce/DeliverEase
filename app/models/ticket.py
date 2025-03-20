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
    user_id: str
    subject: str
    status: str
    created_at: Optional[datetime] = None
    user: Optional[dict] = None
    messages: List[TicketMessage] = field(default_factory=list)
    description: str = ""
    driver_id: str = None
    order_id: str = None
    updates: List['TicketUpdate'] = field(default_factory=list)

    def __init__(self, id: str, subject: str, description: str, status: str, 
                 created_at: datetime, user_id: str = None, driver_id: str = None, 
                 order_id: str = None):
        self.id = id
        self.subject = subject
        self.description = description
        self.status = status
        self.created_at = created_at
        self.user_id = user_id
        self.driver_id = driver_id
        self.order_id = order_id
        self.updates = []  # List of TicketUpdate objects

class TicketUpdate:
    def __init__(self, id: str, ticket_id: str, message: str, created_at: datetime,
                 user_id: str = None, driver_id: str = None):
        self.id = id
        self.ticket_id = ticket_id
        self.message = message
        self.created_at = created_at
        self.user_id = user_id
        self.driver_id = driver_id 