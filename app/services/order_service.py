from typing import List, Optional
from datetime import date, datetime
from supabase import create_client, Client
from ..config import Config
from ..models.order import Order, OrderAssignment, OrderUpdate
from app.utils.supabase_client import get_supabase
import dateutil.parser

class OrderService:
    def __init__(self):
        self.supabase = get_supabase()

    def get_total_orders(self) -> int:
        """Get total number of orders"""
        try:
            response = self.supabase.table('de_orders').select('*', count='exact').execute()
            return response.count
        except Exception as e:
            print(f"Error getting total orders: {e}")
            return 0

    def get_orders_by_status(self, status: str) -> List[Order]:
        """Get orders by status"""
        try:
            response = self.supabase.table('de_orders')\
                .select('*, users!inner(*)')\
                .eq('status', status)\
                .execute()
            return response.data
        except Exception as e:
            print(f"Error getting orders by status: {e}")
            return []

    def create_order(self, user_id: str, pickup_location: str, delivery_location: str, 
                    item_description: str, weight: float, price: float) -> Order:
        try:
            order_data = {
                'user_id': user_id,
                'item_description': item_description,
                'pickup_location': pickup_location,
                'delivery_location': delivery_location,
                'weight': weight,
                'price': price,
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table('de_orders').insert(order_data).execute()
            return response.data[0]
        except Exception as e:
            print(f"Error creating order: {e}")
            return None

    def get_user_orders(self, user_id: str) -> List[Order]:
        """Get orders for a specific user"""
        try:
            response = self.supabase.table('de_orders')\
                .select('''
                    *,
                    de_users!de_orders_driver_id_fkey (
                        id, email, full_name, phone_number
                    )
                ''')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()

            # Convert response data to Order objects
            orders = []
            for order_data in response.data:
                try:
                    order = Order(
                        id=order_data['id'],
                        user_id=order_data['user_id'],
                        pickup_location=order_data['pickup_location'],
                        delivery_location=order_data['delivery_location'],
                        item_description=order_data['item_description'],
                        weight=float(order_data['weight']) if order_data.get('weight') else None,
                        price=float(order_data['price']) if order_data.get('price') else None,
                        status=order_data['status'],
                        driver_id=order_data.get('driver_id'),
                        created_at=datetime.fromisoformat(order_data['created_at']) if order_data.get('created_at') else None,
                        expected_delivery_date=datetime.strptime(order_data['expected_delivery_date'], '%Y-%m-%d').date() if order_data.get('expected_delivery_date') else None,
                        actual_delivery_date=datetime.strptime(order_data['actual_delivery_date'], '%Y-%m-%d').date() if order_data.get('actual_delivery_date') else None
                    )

                    # Add driver data if available
                    if 'de_users' in order_data and order_data['de_users']:
                        order.driver = order_data['de_users']

                    orders.append(order)
                except Exception as e:
                    print(f"Error processing order data: {e}")
                    print(f"Problematic order data: {order_data}")
                    continue

            return orders
        except Exception as e:
            print(f"Error getting user orders: {e}")
            return []

    def get_driver_orders(self, driver_id: str, status: Optional[str] = None) -> List[Order]:
        """Get orders assigned to a driver"""
        try:
            print(f"Fetching orders for driver: {driver_id}")  # Debug log
            
            query = self.supabase.table('de_orders')\
                .select('''
                    *,
                    customer:de_users!de_orders_user_id_fkey (
                        id, email, full_name, phone_number
                    )
                ''')\
                .eq('driver_id', driver_id)
            
            if status:
                query = query.eq('status', status)
            
            response = query.order('created_at', desc=True).execute()
            
            print(f"Raw response data: {response.data}")  # Debug log
            
            if not response.data:
                print("No orders found for driver")  # Debug log
                return []

            # Convert response data to Order objects
            orders = []
            for order_data in response.data:
                try:
                    # Parse dates safely
                    created_at = None
                    expected_delivery_date = None
                    actual_delivery_date = None

                    try:
                        if order_data.get('created_at'):
                            created_at = dateutil.parser.parse(order_data['created_at'])
                    except Exception as e:
                        print(f"Error parsing created_at: {e}")

                    try:
                        if order_data.get('expected_delivery_date'):
                            expected_delivery_date = datetime.strptime(order_data['expected_delivery_date'], '%Y-%m-%d').date()
                    except Exception as e:
                        print(f"Error parsing expected_delivery_date: {e}")

                    try:
                        if order_data.get('actual_delivery_date'):
                            actual_delivery_date = datetime.strptime(order_data['actual_delivery_date'], '%Y-%m-%d').date()
                    except Exception as e:
                        print(f"Error parsing actual_delivery_date: {e}")

                    order = Order(
                        id=order_data['id'],
                        user_id=order_data['user_id'],
                        pickup_location=order_data['pickup_location'],
                        delivery_location=order_data['delivery_location'],
                        item_description=order_data['item_description'],
                        weight=float(order_data['weight']) if order_data.get('weight') else None,
                        price=float(order_data['price']) if order_data.get('price') else None,
                        status=order_data['status'],
                        driver_id=order_data.get('driver_id'),
                        created_at=created_at,
                        expected_delivery_date=expected_delivery_date,
                        actual_delivery_date=actual_delivery_date
                    )

                    # Add customer data if available
                    if 'customer' in order_data and order_data['customer']:
                        order.user = order_data['customer']

                    orders.append(order)
                    print(f"Successfully processed order: {order.id}")  # Debug log
                except Exception as e:
                    print(f"Error processing order data: {e}")
                    print(f"Problematic order data: {order_data}")
                    continue

            print(f"Total orders processed: {len(orders)}")  # Debug log
            return orders
        except Exception as e:
            print(f"Error getting driver orders: {e}")
            return []

    def get_open_orders(self) -> List[Order]:
        """Get all open orders (pending and without driver)"""
        try:
            response = self.supabase.table('de_orders')\
                .select('*')\
                .eq('status', 'pending')\
                .is_('driver_id', 'null')\
                .execute()
            return response.data
        except Exception as e:
            print(f"Error getting open orders: {e}")
            return []

    def update_order_status(self, order_id: str, status: str, driver_id: str = None, message: str = None) -> bool:
        """Update order status and optionally add a status update message"""
        try:
            print(f"Updating order {order_id} to status: {status}")  # Debug log
            
            # Validate status
            valid_statuses = ['pending', 'in_transit', 'delivered', 'cancelled']
            if status not in valid_statuses:
                print(f"Invalid status: {status}")
                return False
            
            # Update order status
            update_data = {
                'status': status
            }
            
            # Add actual delivery date if status is delivered
            if status == 'delivered':
                update_data['actual_delivery_date'] = datetime.utcnow().date().isoformat()
            
            result = self.supabase.table('de_orders')\
                .update(update_data)\
                .eq('id', order_id)\
                .execute()
                
            if not result.data:
                print("No data returned from update operation")
                return False

            # Add status update message if provided
            if message:
                self.add_order_update(order_id, driver_id, status, message)
                
            print(f"Successfully updated order status to {status}")  # Debug log
            return True
            
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False

    def add_order_update(self, order_id: str, driver_id: str, status: str, message: str) -> OrderUpdate:
        """Add an update message to an order"""
        try:
            data = {
                'order_id': order_id,
                'driver_id': driver_id,
                'status': status,
                'update_message': message,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('de_order_updates').insert(data).execute()
            return OrderUpdate(**result.data[0])
        except Exception as e:
            print(f"Error adding order update: {e}")
            return None

    def get_recent_orders(self, limit: int = 5) -> List[Order]:
        """Get recent orders"""
        try:
            response = self.supabase.table('de_orders')\
                .select('*, users!inner(*)')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            print(f"Error getting recent orders: {e}")
            return []

    def assign_order(self, order_id: str, driver_id: str, expected_delivery_date: date) -> Optional[OrderAssignment]:
        """Assign an order to a driver"""
        try:
            # First, create the assignment
            assignment_data = {
                'order_id': order_id,
                'driver_id': driver_id,
                'expected_delivery_date': expected_delivery_date.isoformat(),
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Insert assignment
            result = self.supabase.table('de_order_assignments').insert(assignment_data).execute()
            
            if result.data:
                # Update the order with driver and expected delivery date
                order_update = {
                    'driver_id': driver_id,
                    'expected_delivery_date': expected_delivery_date.isoformat(),
                    'status': 'pending'  # Keep as pending until driver accepts
                }
                self.supabase.table('de_orders')\
                    .update(order_update)\
                    .eq('id', order_id)\
                    .execute()
                
                return OrderAssignment(
                    id=result.data[0]['id'],
                    order_id=order_id,
                    driver_id=driver_id,
                    status='pending',
                    expected_delivery_date=expected_delivery_date,
                    created_at=datetime.utcnow()
                )
            return None
        except Exception as e:
            print(f"Error assigning order: {e}")
            print(f"Full error details: {str(e)}")
            return None

    def get_available_orders(self) -> List[Order]:
        """Get available orders (pending orders with no driver assigned)"""
        try:
            response = self.supabase.table('de_orders')\
                .select('''
                    *,
                    de_users!de_orders_user_id_fkey (
                        id, email, full_name, phone_number
                    )
                ''')\
                .eq('status', 'pending')\
                .is_('driver_id', 'null')\
                .order('created_at', desc=True)\
                .execute()

            # Convert response data to Order objects
            orders = []
            for order_data in response.data:
                try:
                    order = Order(
                        id=order_data['id'],
                        user_id=order_data['user_id'],
                        pickup_location=order_data['pickup_location'],
                        delivery_location=order_data['delivery_location'],
                        item_description=order_data['item_description'],
                        weight=float(order_data['weight']) if order_data.get('weight') else None,
                        price=float(order_data['price']) if order_data.get('price') else None,
                        status=order_data['status'],
                        driver_id=order_data.get('driver_id'),
                        created_at=datetime.fromisoformat(order_data['created_at']) if order_data.get('created_at') else None,
                        expected_delivery_date=datetime.strptime(order_data['expected_delivery_date'], '%Y-%m-%d').date() if order_data.get('expected_delivery_date') else None,
                        actual_delivery_date=datetime.strptime(order_data['actual_delivery_date'], '%Y-%m-%d').date() if order_data.get('actual_delivery_date') else None
                    )

                    # Add user data if available
                    if 'de_users' in order_data and order_data['de_users']:
                        order.user = order_data['de_users']

                    orders.append(order)
                except Exception as e:
                    print(f"Error processing order data: {e}")
                    print(f"Problematic order data: {order_data}")
                    continue

            return orders
        except Exception as e:
            print(f"Error getting available orders: {e}")
            return []

    def get_all_orders(self, status: Optional[str] = None) -> List[Order]:
        """Get all orders, optionally filtered by status"""
        try:
            query = self.supabase.table('de_orders')\
                .select('''
                    *,
                    de_users!de_orders_user_id_fkey (
                        id,
                        email,
                        full_name,
                        phone_number
                    ),
                    driver:de_users!de_orders_driver_id_fkey (
                        id,
                        email,
                        full_name,
                        phone_number
                    )
                ''')\
                .order('created_at', desc=True)
            
            if status:
                query = query.eq('status', status)
            
            response = query.execute()
            
            # Convert response data to Order objects
            orders = []
            for order_data in response.data:
                try:
                    # Create order object with base fields
                    order = Order(
                        id=order_data['id'],
                        user_id=order_data['user_id'],
                        pickup_location=order_data['pickup_location'],
                        delivery_location=order_data['delivery_location'],
                        item_description=order_data['item_description'],
                        weight=float(order_data['weight']) if order_data.get('weight') else None,
                        price=float(order_data['price']) if order_data.get('price') else None,
                        status=order_data['status'],
                        driver_id=order_data.get('driver_id'),
                        created_at=datetime.fromisoformat(order_data['created_at']) if order_data.get('created_at') else None,
                        expected_delivery_date=datetime.strptime(order_data['expected_delivery_date'], '%Y-%m-%d').date() if order_data.get('expected_delivery_date') else None,
                        actual_delivery_date=datetime.strptime(order_data['actual_delivery_date'], '%Y-%m-%d').date() if order_data.get('actual_delivery_date') else None
                    )

                    # Add user data if available
                    if 'de_users' in order_data and order_data['de_users']:
                        order.user = order_data['de_users']

                    # Add driver data if available
                    if 'driver' in order_data and order_data['driver']:
                        order.driver = order_data['driver']

                    orders.append(order)
                except Exception as e:
                    print(f"Error processing order data: {e}")
                    print(f"Problematic order data: {order_data}")
                    continue
            
            return orders
        except Exception as e:
            print(f"Error getting all orders: {e}")
            return []

    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by ID with all related information"""
        try:
            response = self.supabase.table('de_orders')\
                .select('''
                    *,
                    de_users!de_orders_user_id_fkey (
                        id, email, full_name, phone_number
                    ),
                    driver:de_users!de_orders_driver_id_fkey (
                        id, email, full_name, phone_number
                    )
                ''')\
                .eq('id', order_id)\
                .execute()
            
            if not response.data:
                return None
            
            order_data = response.data[0]
            order = Order(
                id=order_data['id'],
                user_id=order_data['user_id'],
                pickup_location=order_data['pickup_location'],
                delivery_location=order_data['delivery_location'],
                item_description=order_data['item_description'],
                weight=float(order_data['weight']) if order_data.get('weight') else None,
                price=float(order_data['price']) if order_data.get('price') else None,
                status=order_data['status'],
                driver_id=order_data.get('driver_id'),
                created_at=datetime.fromisoformat(order_data['created_at']) if order_data.get('created_at') else None,
                expected_delivery_date=datetime.strptime(order_data['expected_delivery_date'], '%Y-%m-%d').date() if order_data.get('expected_delivery_date') else None,
                actual_delivery_date=datetime.strptime(order_data['actual_delivery_date'], '%Y-%m-%d').date() if order_data.get('actual_delivery_date') else None
            )

            # Add user and driver details if available
            if 'de_users' in order_data and order_data['de_users']:
                order.user = order_data['de_users']
            if 'driver' in order_data and order_data['driver']:
                order.driver = order_data['driver']

            return order
        except Exception as e:
            print(f"Error getting order by ID: {e}")
            return None 