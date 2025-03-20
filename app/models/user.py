from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from flask_login import UserMixin

@dataclass
class User(UserMixin):
    id: str
    email: str
    user_type: str
    full_name: str
    phone_number: Optional[str] = None
    created_at: datetime = None
    last_login: datetime = None

    def __post_init__(self):
        self.id = str(self.id)
        self.email = str(self.email)
        self.user_type = str(self.user_type)
        self.full_name = str(self.full_name)

    def get_id(self):
        """Required by Flask-Login"""
        return str(self.id)

    @property
    def is_authenticated(self):
        """Required by Flask-Login"""
        return True

    @property
    def is_active(self):
        """Required by Flask-Login"""
        return True

    @property
    def is_anonymous(self):
        """Required by Flask-Login"""
        return False

@dataclass
class DriverDetails:
    id: str
    user_id: str
    vehicle_type: str
    license_number: str
    current_location: str
    is_available: bool = True
    created_at: datetime = None 