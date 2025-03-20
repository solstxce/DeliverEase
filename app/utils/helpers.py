from datetime import datetime
import re

def validate_email(email):
    """Validate email format"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def format_datetime(dt):
    """Format datetime for JSON response"""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt

def validate_phone_number(phone):
    """Validate phone number format"""
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone))

def sanitize_input(text):
    """Basic input sanitization"""
    if not text:
        return text
    # Remove any HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove any script tags and their contents
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
    return text.strip() 