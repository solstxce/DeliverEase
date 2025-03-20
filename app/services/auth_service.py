from typing import Optional, List
from app.utils.supabase_client import get_supabase
from werkzeug.security import check_password_hash, generate_password_hash
from ..config import Config
from ..models.user import User

class AuthService:
    def __init__(self):
        self.supabase = get_supabase()

    def register_user(self, email: str, password: str, user_type: str, full_name: str, phone_number: Optional[str] = None) -> User:
        try:
            # Check if user exists
            response = self.supabase.table('de_users').select('*').eq('email', email).execute()
            if response.data:
                return None, "Email already registered"

            # Create new user
            password_hash = generate_password_hash(password)
            user_data = {
                'email': email,
                'password_hash': password_hash,
                'user_type': user_type,
                'full_name': full_name,
                'phone_number': phone_number,
                'is_active': True
            }
            
            response = self.supabase.table('de_users').insert(user_data).execute()
            return response.data[0], None
        except Exception as e:
            print(f"Registration error: {e}")
            return None, str(e)

    def login(self, email: str, password: str) -> Optional[User]:
        try:
            # Query user from Supabase
            response = self.supabase.table('de_users').select('*').eq('email', email).execute()
            
            if not response.data:
                print("No user found with this email")
                return None
            
            user_data = response.data[0]
            print(f"Found user: {user_data['email']}")
            
            # Check password using werkzeug's check_password_hash
            if check_password_hash(user_data['password_hash'], password):
                # Update last login
                self.supabase.table('de_users').update({
                    'last_login': 'now()'
                }).eq('id', user_data['id']).execute()
                
                # Create User object with all required fields
                user = User(
                    id=user_data['id'],
                    email=user_data['email'],
                    user_type=user_data['user_type'],
                    full_name=user_data['full_name'],
                    phone_number=user_data.get('phone_number'),
                    created_at=user_data.get('created_at'),
                    last_login=user_data.get('last_login')
                )
                print(f"Login successful for user: {user.email}")
                return user
            
            print("Password verification failed")
            return None
        except Exception as e:
            print(f"Login error: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            response = self.supabase.table('de_users').select('*').eq('id', user_id).execute()
            if response.data:
                user_data = response.data[0]
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    user_type=user_data['user_type'],
                    full_name=user_data['full_name'],
                    phone_number=user_data.get('phone_number'),
                    created_at=user_data.get('created_at'),
                    last_login=user_data.get('last_login')
                )
            return None
        except Exception as e:
            print(f"Get user error: {e}")
            return None

    def get_total_users(self) -> int:
        """Get total number of users"""
        try:
            response = self.supabase.table('de_users').select('*', count='exact').execute()
            return response.count
        except Exception as e:
            print(f"Error getting total users: {e}")
            return 0

    def get_users_by_type(self, user_type: str) -> List[User]:
        """Get users filtered by type"""
        try:
            response = self.supabase.table('de_users')\
                .select('*')\
                .eq('user_type', user_type)\
                .execute()
            return response.data
        except Exception as e:
            print(f"Error getting users by type: {e}")
            return []

    def get_users(self, user_type: Optional[str] = None) -> List[User]:
        """Get all users, optionally filtered by type"""
        try:
            query = self.supabase.table('de_users').select('*')
            if user_type:
                query = query.eq('user_type', user_type)
            
            response = query.execute()
            return [User(
                id=user['id'],
                email=user['email'],
                user_type=user['user_type'],
                full_name=user['full_name'],
                phone_number=user.get('phone_number'),
                created_at=user.get('created_at'),
                last_login=user.get('last_login')
            ) for user in response.data]
        except Exception as e:
            print(f"Error getting users: {e}")
            return [] 