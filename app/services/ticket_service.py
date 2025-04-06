from typing import List, Optional
from app.utils.supabase_client import get_supabase
from ..config import Config
from ..models.ticket import Ticket, TicketMessage, TicketUpdate
from datetime import datetime
import dateutil.parser

class TicketService:
    def __init__(self):
        self.supabase = get_supabase()

    def get_total_tickets(self) -> int:
        """Get total number of tickets"""
        try:
            response = self.supabase.table('de_tickets').select('*', count='exact').execute()
            return response.count
        except Exception as e:
            print(f"Error getting total tickets: {e}")
            return 0

    def get_tickets_by_status(self, status: Optional[str] = None) -> List[Ticket]:
        """Get tickets filtered by status"""
        try:
            query = self.supabase.table('de_tickets')\
                .select('*, de_users!inner(*)')\
                .order('created_at', desc=True)
            
            if status:
                query = query.eq('status', status)
            
            response = query.execute()
            
            # Transform raw data into properly structured ticket objects
            tickets = []
            for ticket_data in response.data:
                # Create a ticket object with user property
                ticket = {
                    'id': ticket_data['id'],
                    'subject': ticket_data['subject'],
                    'status': ticket_data['status'],
                    'created_at': dateutil.parser.parse(ticket_data['created_at']) if ticket_data.get('created_at') else None,
                    'updated_at': dateutil.parser.parse(ticket_data['updated_at']) if ticket_data.get('updated_at') else None,
                    'user': {
                        'id': ticket_data.get('de_users', {}).get('id'),
                        'full_name': ticket_data.get('de_users', {}).get('full_name'),
                        'email': ticket_data.get('de_users', {}).get('email')
                    }
                }
                tickets.append(ticket)
            
            return tickets
        except Exception as e:
            print(f"Error getting tickets by status: {e}")
            # Print the exact error details to help with debugging
            if hasattr(e, 'json'):
                error_details = e.json()
                print(f"Detailed error: {error_details}")
            return []

    def create_ticket(self, user_id: str, subject: str, message: str) -> Ticket:
        """Create a new support ticket"""
        try:
            # Create ticket
            ticket_data = {
                'user_id': user_id,
                'subject': subject,
                'status': 'open',
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('de_tickets').insert(ticket_data).execute()
            ticket_id = result.data[0]['id']
            
            # Add initial message
            message_data = {
                'ticket_id': ticket_id,
                'sender_id': user_id,
                'message': message,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('de_ticket_messages').insert(message_data).execute()
            return result.data[0]
        except Exception as e:
            print(f"Error creating ticket: {e}")
            return None

    def get_user_tickets(self, user_id: str) -> List[Ticket]:
        """Get tickets for a specific user"""
        try:
            response = self.supabase.table('de_tickets')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            return response.data
        except Exception as e:
            print(f"Error getting user tickets: {e}")
            return []

    def get_ticket_messages(self, ticket_id: str) -> List[dict]:
        """Get messages for a specific ticket"""
        try:
            # First, get the messages without trying to join
            response = self.supabase.table('de_ticket_messages')\
                .select('*')\
                .eq('ticket_id', ticket_id)\
                .order('created_at')\
                .execute()
            
            if not response.data:
                return []
            
            # Process messages and fetch sender information
            messages = []
            for msg_data in response.data:
                # Create basic message structure
                message = {
                    'id': msg_data['id'],
                    'message': msg_data['message'],
                    'created_at': dateutil.parser.parse(msg_data['created_at']) if msg_data.get('created_at') else None,
                    'sender': None
                }
                
                # Get sender info separately to avoid join issues
                if msg_data.get('sender_id'):
                    user_response = self.supabase.table('de_users')\
                        .select('*')\
                        .eq('id', msg_data['sender_id'])\
                        .execute()
                        
                    if user_response.data:
                        message['sender'] = {
                            'id': user_response.data[0]['id'],
                            'full_name': user_response.data[0]['full_name'],
                            'email': user_response.data[0]['email'],
                            'user_type': user_response.data[0]['user_type']
                        }
                
                messages.append(message)
            
            return messages
        except Exception as e:
            print(f"Error getting ticket messages: {e}")
            # Print the detailed error for debugging
            if hasattr(e, 'json'):
                error_details = e.json()
                print(f"Detailed error: {error_details}")
            return []

    def add_message(self, ticket_id: str, sender_id: str, message: str) -> TicketMessage:
        """Add a message to a ticket"""
        try:
            message_data = {
                'ticket_id': ticket_id,
                'sender_id': sender_id,
                'message': message,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('de_ticket_messages').insert(message_data).execute()
            return result.data[0]
        except Exception as e:
            print(f"Error adding message: {e}")
            return None

    def close_ticket(self, ticket_id: str) -> bool:
        """Close a support ticket"""
        try:
            self.supabase.table('de_tickets').update({
                'status': 'closed',
                'closed_at': datetime.utcnow().isoformat()
            }).eq('id', ticket_id).execute()
            return True
        except Exception as e:
            print(f"Error closing ticket: {e}")
            return False

    def get_recent_tickets(self, limit: int = 5) -> List[Ticket]:
        """Get recent tickets"""
        try:
            response = self.supabase.table('de_tickets')\
                .select('*, users!inner(*)')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            print(f"Error getting recent tickets: {e}")
            return []

    def get_open_tickets_count(self) -> int:
        """Get count of open tickets"""
        try:
            response = self.supabase.table('de_tickets')\
                .select('*', count='exact')\
                .eq('status', 'open')\
                .execute()
            return response.count
        except Exception as e:
            print(f"Error getting open tickets count: {e}")
            return 0

    def get_ticket_by_id(self, ticket_id: str) -> Optional[dict]:
        """Get a ticket by its ID with messages"""
        try:
            # Get the ticket with user information
            # First try to get the ticket without a join
            ticket_response = self.supabase.table('de_tickets')\
                .select('*')\
                .eq('id', ticket_id)\
                .execute()
            
            if not ticket_response.data:
                return None
            
            ticket_data = ticket_response.data[0]
            
            # Get the user information separately
            user_id = ticket_data.get('user_id')
            user_info = {'id': user_id, 'full_name': 'Unknown', 'email': 'unknown@example.com'}
            
            if user_id:
                user_response = self.supabase.table('de_users')\
                    .select('*')\
                    .eq('id', user_id)\
                    .execute()
                    
                if user_response.data:
                    user_info = {
                        'id': user_response.data[0]['id'],
                        'full_name': user_response.data[0]['full_name'],
                        'email': user_response.data[0]['email'],
                        'user_type': user_response.data[0]['user_type']
                    }
            
            # Create the ticket object
            ticket = {
                'id': ticket_data['id'],
                'subject': ticket_data['subject'],
                'status': ticket_data['status'],
                'created_at': dateutil.parser.parse(ticket_data['created_at']) if ticket_data.get('created_at') else None,
                'updated_at': dateutil.parser.parse(ticket_data['updated_at']) if ticket_data.get('updated_at') else None,
                'user': user_info,
                'messages': []
            }
            
            # Get the messages for this ticket
            messages = self.get_ticket_messages(ticket_id)
            ticket['messages'] = messages
            
            return ticket
        except Exception as e:
            print(f"Error getting ticket by ID: {e}")
            if hasattr(e, 'json'):
                error_details = e.json()
                print(f"Detailed error: {error_details}")
            return None

    def get_driver_tickets(self, driver_id: str) -> List[Ticket]:
        """Get all tickets associated with a driver"""
        try:
            # Query tickets table with driver_id
            response = self.supabase.table('de_tickets') \
                .select('*') \
                .eq('driver_id', driver_id) \
                .order('created_at', desc=True) \
                .execute()

            if not response.data:
                return []

            # Convert response data to Ticket objects
            tickets = []
            for ticket_data in response.data:
                ticket = Ticket(
                    id=ticket_data['id'],
                    subject=ticket_data['subject'],
                    description=ticket_data['description'],
                    status=ticket_data['status'],
                    created_at=dateutil.parser.parse(ticket_data['created_at']),
                    user_id=ticket_data['user_id'],
                    driver_id=ticket_data['driver_id'],
                    order_id=ticket_data['order_id'] if 'order_id' in ticket_data else None
                )
                
                # Get ticket updates if any
                updates_response = self.supabase.table('de_ticket_updates') \
                    .select('*') \
                    .eq('ticket_id', ticket.id) \
                    .order('created_at', desc=True) \
                    .execute()
                    
                if updates_response.data:
                    ticket.updates = [
                        TicketUpdate(
                            id=update['id'],
                            ticket_id=update['ticket_id'],
                            message=update['message'],
                            created_at=dateutil.parser.parse(update['created_at']),
                            user_id=update['user_id'] if 'user_id' in update else None,
                            driver_id=update['driver_id'] if 'driver_id' in update else None
                        )
                        for update in updates_response.data
                    ]
                
                tickets.append(ticket)

            return tickets

        except Exception as e:
            print(f"Error getting driver tickets: {e}")
            return []

    def create_driver_ticket(self, driver_id: str, subject: str, description: str, order_id: Optional[str] = None) -> Optional[Ticket]:
        """Create a new ticket for a driver"""
        try:
            ticket_data = {
                'driver_id': driver_id,
                'subject': subject,
                'description': description,
                'status': 'open',
                'created_at': datetime.utcnow().isoformat(),
                'order_id': order_id
            }
            
            result = self.supabase.table('de_tickets').insert(ticket_data).execute()
            
            if result.data:
                return Ticket(
                    id=result.data[0]['id'],
                    subject=subject,
                    description=description,
                    status='open',
                    created_at=datetime.utcnow(),
                    driver_id=driver_id,
                    order_id=order_id
                )
            return None
        
        except Exception as e:
            print(f"Error creating driver ticket: {e}")
            return None

    def get_all_tickets(self, status: Optional[str] = None) -> List[Ticket]:
        """Alias for get_tickets_by_status for backward compatibility"""
        return self.get_tickets_by_status(status)

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Alias for get_ticket_by_id for backward compatibility"""
        return self.get_ticket_by_id(ticket_id) 