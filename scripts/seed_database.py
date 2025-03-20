from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def create_user(email, password, user_type, full_name, phone_number):
    """Create a user and return their ID"""
    try:
        user_data = {
            'id': str(uuid.uuid4()),
            'email': email,
            'password_hash': generate_password_hash(password),
            'user_type': user_type,
            'full_name': full_name,
            'phone_number': phone_number,
            'created_at': datetime.utcnow().isoformat(),
            'last_login': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('de_users').insert(user_data).execute()
        return result.data[0]['id']
    except Exception as e:
        print(f"Error creating user {email}: {str(e)}")
        return None

def create_driver_details(user_id, vehicle_type, license_number, current_location):
    """Create driver details for a user"""
    try:
        driver_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'vehicle_type': vehicle_type,
            'license_number': license_number,
            'current_location': current_location,
            'is_available': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('de_driver_details').insert(driver_data).execute()
    except Exception as e:
        print(f"Error creating driver details for {user_id}: {str(e)}")

def create_order(user_id, pickup_location, delivery_location, item_description, weight, price):
    """Create a sample order"""
    try:
        order_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'pickup_location': pickup_location,
            'delivery_location': delivery_location,
            'item_description': item_description,
            'weight': weight,
            'price': price,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('de_orders').insert(order_data).execute()
    except Exception as e:
        print(f"Error creating order: {str(e)}")

def create_ticket(user_id, subject, message):
    """Create a support ticket with an initial message"""
    try:
        # Create ticket
        ticket_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'subject': subject,
            'status': 'open',
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('de_tickets').insert(ticket_data).execute()
        ticket_id = result.data[0]['id']
        
        # Create initial message
        message_data = {
            'id': str(uuid.uuid4()),
            'ticket_id': ticket_id,
            'sender_id': user_id,
            'message': message,
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('de_ticket_messages').insert(message_data).execute()
    except Exception as e:
        print(f"Error creating ticket: {str(e)}")

def seed_database():
    """Main function to seed the database"""
    print("Starting database seeding...")

    # Create admin user
    print("Creating admin user...")
    admin_id = create_user(
        email='admin@deliverease.com',
        password='admin123',
        user_type='admin',
        full_name='Admin User',
        phone_number='+1234567890'
    )

    # Create regular user
    print("Creating regular user...")
    user_id = create_user(
        email='user@deliverease.com',
        password='user123',
        user_type='user',
        full_name='John Doe',
        phone_number='+1987654321'
    )

    # Create driver user
    print("Creating driver user...")
    driver_id = create_user(
        email='driver@deliverease.com',
        password='driver123',
        user_type='driver',
        full_name='Mike Smith',
        phone_number='+1122334455'
    )

    # Create driver details
    if driver_id:
        print("Creating driver details...")
        create_driver_details(
            user_id=driver_id,
            vehicle_type='Van',
            license_number='DL123456',
            current_location='New York, NY'
        )

    # Create sample order
    if user_id:
        print("Creating sample order...")
        create_order(
            user_id=user_id,
            pickup_location='123 Main St, New York, NY',
            delivery_location='456 Park Ave, New York, NY',
            item_description='Package containing books',
            weight=2.5,
            price=25.00
        )

        # Create sample support ticket
        print("Creating sample support ticket...")
        create_ticket(
            user_id=user_id,
            subject='Delivery Delay Question',
            message='When will my package arrive?'
        )

    print("Database seeding completed!")

if __name__ == "__main__":
    seed_database() 