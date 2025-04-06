from typing import Optional, List, Tuple
from app.utils.supabase_client import get_supabase
from werkzeug.security import check_password_hash, generate_password_hash
from ..config import Config
from ..models.user import User
import logging
import time
import socket

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.supabase = get_supabase()
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def _execute_with_retry(self, operation_func, *args, **kwargs):
        """Execute a Supabase operation with retry logic"""
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                return operation_func(*args, **kwargs), None
            except (socket.gaierror, ConnectionError) as e:
                retries += 1
                last_error = e
                logger.warning(f"Connection error (attempt {retries}/{self.max_retries}): {e}")
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Operation error: {e}")
                return None, str(e)
                
        logger.error(f"Failed after {self.max_retries} attempts: {last_error}")
        return None, f"Connection error: {last_error}"

    def register_user(self, email: str, password: str, user_type: str, full_name: str, phone_number: Optional[str] = None) -> Tuple[Optional[User], Optional[str]]:
        logger.info(f"Attempting to register user: {email}")
        
        # Validate user_type
        if user_type not in ['user', 'driver']:
            return None, "Invalid user type. Only 'user' and 'driver' are allowed."
        
        try:
            # Check if user exists
            def check_user_exists():
                return self.supabase.table('de_users').select('*').eq('email', email).execute()
            
            response, error = self._execute_with_retry(check_user_exists)
            if error:
                return None, f"Error checking user existence: {error}"
            
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
            
            def create_user():
                return self.supabase.table('de_users').insert(user_data).execute()
            
            response, error = self._execute_with_retry(create_user)
            if error:
                return None, f"Error creating user: {error}"
            
            logger.info(f"Successfully registered user: {email}")
            return response.data[0], None
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return None, str(e)

    def login(self, email: str, password: str) -> Optional[User]:
        logger.info(f"Login attempt for user: {email}")
        try:
            # Query user from Supabase
            def get_user():
                return self.supabase.table('de_users').select('*').eq('email', email).execute()
            
            response, error = self._execute_with_retry(get_user)
            if error:
                logger.error(f"Error fetching user data: {error}")
                return None
            
            if not response.data:
                logger.info("No user found with this email")
                return None
            
            user_data = response.data[0]
            logger.info(f"Found user: {user_data['email']}")
            
            # Check password using werkzeug's check_password_hash
            if check_password_hash(user_data['password_hash'], password):
                # Update last login
                def update_last_login():
                    return self.supabase.table('de_users').update({
                        'last_login': 'now()'
                    }).eq('id', user_data['id']).execute()
                
                self._execute_with_retry(update_last_login)
                
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
                logger.info(f"Login successful for user: {user.email}")
                return user
            
            logger.info("Password verification failed")
            return None
        except Exception as e:
            logger.error(f"Login error: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        logger.info(f"Fetching user with ID: {user_id}")
        try:
            def fetch_user():
                return self.supabase.table('de_users').select('*').eq('id', user_id).execute()
            
            response, error = self._execute_with_retry(fetch_user)
            if error:
                logger.error(f"Error fetching user: {error}")
                return None
            
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
            logger.error(f"Get user error: {e}")
            return None

    def get_total_users(self) -> int:
        """Get total number of users"""
        logger.info("Fetching total user count")
        try:
            def count_users():
                return self.supabase.table('de_users').select('*', count='exact').execute()
            
            response, error = self._execute_with_retry(count_users)
            if error:
                logger.error(f"Error counting users: {error}")
                return 0
                
            return response.count
        except Exception as e:
            logger.error(f"Error getting total users: {e}")
            return 0

    def get_users_by_type(self, user_type: str) -> List[User]:
        """Get users filtered by type"""
        logger.info(f"Fetching users with type: {user_type}")
        try:
            def fetch_users_by_type():
                return self.supabase.table('de_users')\
                    .select('*')\
                    .eq('user_type', user_type)\
                    .execute()
            
            response, error = self._execute_with_retry(fetch_users_by_type)
            if error:
                logger.error(f"Error fetching users by type: {error}")
                return []
                
            return response.data
        except Exception as e:
            logger.error(f"Error getting users by type: {e}")
            return []

    def get_users(self, user_type: Optional[str] = None) -> List[User]:
        """Get all users, optionally filtered by type"""
        logger.info(f"Fetching all users{' filtered by type: ' + user_type if user_type else ''}")
        try:
            def fetch_users():
                query = self.supabase.table('de_users').select('*')
                if user_type:
                    query = query.eq('user_type', user_type)
                return query.execute()
            
            response, error = self._execute_with_retry(fetch_users)
            if error:
                logger.error(f"Error fetching users: {error}")
                return []
                
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
            logger.error(f"Error getting users: {e}")
            return [] 