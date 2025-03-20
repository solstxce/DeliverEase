from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services.auth_service import AuthService
from app.services.order_service import OrderService
from app.services.ticket_service import TicketService
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint('admin', __name__, url_prefix='/admin')
auth_service = AuthService()
order_service = OrderService()
ticket_service = TicketService()

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type != 'admin':
        return redirect_user_by_type(current_user)
    
    # Get summary statistics
    stats = {
        'total_users': auth_service.get_total_users(),
        'total_orders': order_service.get_total_orders(),
        'open_tickets': ticket_service.get_open_tickets_count(),
        'recent_orders': order_service.get_recent_orders(5),
        'recent_tickets': ticket_service.get_recent_tickets(5)
    }
    
    # Get activity data
    recent_activity = []
    
    # Add recent orders to activity
    for order in stats['recent_orders']:
        recent_activity.append({
            'type': 'order',
            'description': f"New order created",
            'details': f"From {order['pickup_location']} to {order['delivery_location']}",
            'timestamp': datetime.fromisoformat(order['created_at'])
        })
    
    # Add recent tickets to activity
    for ticket in stats['recent_tickets']:
        recent_activity.append({
            'type': 'ticket',
            'description': f"New support ticket",
            'details': ticket['subject'],
            'timestamp': datetime.fromisoformat(ticket['created_at'])
        })
    
    # Sort activity by timestamp
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_activity=recent_activity[:10])  # Show only last 10 activities

@bp.route('/users')
@login_required
def users():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('user.dashboard'))
    
    user_type = request.args.get('type')
    users = auth_service.get_users(user_type=user_type)
    return render_template('admin/users.html', users=users)

@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        user, error = auth_service.register_user(
            email=request.form.get('email'),
            password=request.form.get('password'),
            user_type=request.form.get('user_type'),
            full_name=request.form.get('full_name'),
            phone_number=request.form.get('phone_number')
        )
        
        if user:
            flash('User created successfully.', 'success')
            return redirect(url_for('admin.users'))
        flash(error or 'Failed to create user.', 'error')
    
    return render_template('admin/user_form.html')

@bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('user.dashboard'))
    
    user = auth_service.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        updated = auth_service.update_user(
            user_id=user_id,
            full_name=request.form.get('full_name'),
            email=request.form.get('email'),
            user_type=request.form.get('user_type'),
            phone_number=request.form.get('phone_number')
        )
        
        if updated:
            flash('User updated successfully.', 'success')
            return redirect(url_for('admin.users'))
        flash('Failed to update user.', 'error')
    
    return render_template('admin/user_form.html', user=user)

@bp.route('/orders')
@login_required
def orders():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('user.dashboard'))
    
    status = request.args.get('status')
    orders = order_service.get_all_orders(status=status)
    return render_template('admin/orders.html', orders=orders)

@bp.route('/orders/<order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('user.dashboard'))
    
    if order_service.update_order_status(order_id, 'cancelled', current_user.id, 'Cancelled by admin'):
        flash('Order cancelled successfully.', 'success')
    else:
        flash('Failed to cancel order.', 'error')
    return redirect(url_for('admin.orders'))

@bp.route('/tickets')
@login_required
def tickets():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('user.dashboard'))
    
    status = request.args.get('status')
    tickets = ticket_service.get_all_tickets(status=status)
    return render_template('admin/tickets.html', tickets=tickets)

@bp.route('/tickets/<ticket_id>/close', methods=['POST'])
@login_required
def close_ticket(ticket_id):
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('user.dashboard'))
    
    if ticket_service.close_ticket(ticket_id):
        flash('Ticket closed successfully.', 'success')
    else:
        flash('Failed to close ticket.', 'error')
    return redirect(url_for('admin.tickets'))

@bp.route('/orders/<order_id>')
@login_required
def view_order(order_id):
    order_service = OrderService()
    order = order_service.get_order_by_id(order_id)
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('admin.orders'))
    return render_template('admin/order_details.html', order=order)

@bp.route('/orders/<order_id>/assign-driver', methods=['POST'])
@login_required
def assign_driver(order_id):
    driver_id = request.form.get('driver_id')
    expected_delivery_date = request.form.get('expected_delivery_date')
    
    if not driver_id or not expected_delivery_date:
        flash('Driver and expected delivery date are required', 'error')
        return redirect(url_for('admin.view_order', order_id=order_id))
    
    try:
        order_service = OrderService()
        # Convert string date to datetime.date
        delivery_date = datetime.strptime(expected_delivery_date, '%Y-%m-%d').date()
        
        # Assign the driver
        assignment = order_service.assign_order(order_id, driver_id, delivery_date)
        if assignment:
            # Update order status
            order_service.update_order_status(
                order_id=order_id,
                status='assigned',
                driver_id=driver_id
            )
            flash('Driver assigned successfully', 'success')
        else:
            flash('Failed to assign driver', 'error')
    except Exception as e:
        print(f"Error assigning driver: {e}")
        flash('An error occurred while assigning the driver', 'error')
    
    return redirect(url_for('admin.view_order', order_id=order_id))

@bp.route('/available-drivers')
@login_required
def get_available_drivers():
    auth_service = AuthService()
    drivers = auth_service.get_users(user_type='driver')
    return jsonify([{
        'id': driver.id,
        'full_name': driver.full_name,
        'email': driver.email
    } for driver in drivers])

@bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    try:
        # Get form data
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        # Validate current password
        if not current_password or not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect', 'error')
            return redirect(request.referrer)

        # Prepare update data
        update_data = {
            'full_name': full_name,
            'phone_number': phone_number
        }

        # Add new password if provided
        if new_password:
            update_data['password_hash'] = generate_password_hash(new_password)

        # Update user profile
        auth_service = AuthService()
        if auth_service.update_user(current_user.id, **update_data):
            flash('Profile updated successfully', 'success')
        else:
            flash('Failed to update profile', 'error')

    except Exception as e:
        print(f"Error updating profile: {e}")
        flash('An error occurred while updating profile', 'error')

    return redirect(request.referrer) 