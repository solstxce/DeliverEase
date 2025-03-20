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
                .select('*, users!inner(*)')\
                .order('created_at', desc=True)
            
            if status:
                query = query.eq('status', status)
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error getting tickets by status: {e}")
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

    def get_ticket_messages(self, ticket_id: str) -> List[TicketMessage]:
        """Get messages for a specific ticket"""
        try:
            response = self.supabase.table('de_ticket_messages')\
                .select('*, users!sender_id(*)')\
                .eq('ticket_id', ticket_id)\
                .order('created_at')\
                .execute()
            return response.data
        except Exception as e:
            print(f"Error getting ticket messages: {e}")
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

    def get_ticket_by_id(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by ID with all related information"""
        try:
            response = self.supabase.table('de_tickets')\
                .select('''
                    *,
                    de_users!de_tickets_user_id_fkey (
                        id, email, full_name, user_type
                    ),
                    de_ticket_messages (
                        *,
                        sender:de_users (
                            id, email, full_name, user_type
                        )
                    )
                ''')\
                .eq('id', ticket_id)\
                .execute()
            
            if not response.data:
                return None
            
            ticket_data = response.data[0]
            
            # Create ticket object without message field
            ticket = Ticket(
                id=ticket_data['id'],
                user_id=ticket_data['user_id'],
                subject=ticket_data['subject'],
                status=ticket_data['status'],
                created_at=dateutil.parser.parse(ticket_data['created_at']) if ticket_data.get('created_at') else None
            )
            
            # Add user data if available
            if 'de_users' in ticket_data and ticket_data['de_users']:
                ticket.user = ticket_data['de_users']
            
            # Add messages if available
            if 'de_ticket_messages' in ticket_data:
                ticket.messages = []
                for message_data in ticket_data['de_ticket_messages']:
                    message = TicketMessage(
                        id=message_data['id'],
                        ticket_id=message_data['ticket_id'],
                        sender_id=message_data['sender_id'],
                        message=message_data['message'],
                        created_at=dateutil.parser.parse(message_data['created_at']) if message_data.get('created_at') else None
                    )
                    if 'sender' in message_data and message_data['sender']:
                        message.sender = message_data['sender']
                    ticket.messages.append(message)
                
                # Sort messages by creation date
                ticket.messages.sort(key=lambda x: x.created_at if x.created_at else datetime.min)
            
            return ticket
        except Exception as e:
            print(f"Error getting ticket by ID: {e}")
            print(f"Ticket data: {ticket_data}")  # For debugging
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