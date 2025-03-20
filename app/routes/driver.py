from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from ..services.order_service import OrderService
from ..services.ticket_service import TicketService
from flask_login import login_required, current_user
from ..utils.decorators import driver_required
from datetime import datetime

bp = Blueprint('driver', __name__, url_prefix='/driver')
order_service = OrderService()
ticket_service = TicketService()

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type != 'driver':
        return redirect_user_by_type(current_user)
    active_deliveries = order_service.get_driver_orders(current_user.id, status='in_transit')
    available_orders = order_service.get_open_orders()
    return render_template('driver/dashboard.html', active_deliveries=active_deliveries, available_orders=available_orders)

@bp.route('/available-orders')
@login_required
def available_orders():
    if current_user.user_type != 'driver':
        flash('Access denied.', 'error')
        return redirect(url_for('user.dashboard'))
        
    orders = order_service.get_available_orders()
    return render_template('driver/available_orders.html', orders=orders)

@bp.route('/my-deliveries')
@login_required
@driver_required
def my_deliveries():
    try:
        # Get orders assigned to this driver
        orders = order_service.get_driver_orders(current_user.id)
        print(f"Driver orders fetched: {len(orders)}")  # Debug log
        print(f"Driver ID: {current_user.id}")  # Debug log
        
        return render_template('driver/my_deliveries.html', orders=orders)
    except Exception as e:
        print(f"Error in my_deliveries route: {e}")  # Debug log
        flash('Error loading deliveries', 'error')
        return render_template('driver/my_deliveries.html', orders=[])

@bp.route('/tickets')
@login_required
@driver_required
def tickets():
    # Get tickets for this driver
    tickets = ticket_service.get_driver_tickets(current_user.id)
    return render_template('driver/tickets.html', tickets=tickets)

@bp.route('/tickets/<ticket_id>')
@login_required
@driver_required
def view_ticket(ticket_id):
    ticket = ticket_service.get_ticket_by_id(ticket_id)
    
    if not ticket:
        flash('Ticket not found', 'error')
        return redirect(url_for('driver.tickets'))
    
    # Ensure drivers can only view their assigned tickets
    if ticket.driver_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('driver.tickets'))
        
    return render_template('driver/ticket_details.html', ticket=ticket)

@bp.route('/accept-order/<order_id>', methods=['POST'])
@login_required
def accept_order(order_id):
    if current_user.user_type != 'driver':
        flash('Access denied.', 'error')
        return redirect(url_for('user.dashboard'))
    
    expected_delivery_date = request.form.get('expected_delivery_date')
    if not expected_delivery_date:
        flash('Expected delivery date is required.', 'error')
        return redirect(url_for('driver.available_orders'))
    
    # Create order assignment
    assignment = order_service.assign_order(
        order_id=order_id,
        driver_id=current_user.id,
        expected_delivery_date=datetime.strptime(expected_delivery_date, '%Y-%m-%d').date()
    )
    
    if assignment:
        flash('Order accepted successfully.', 'success')
        return redirect(url_for('driver.my_deliveries'))
    
    flash('Failed to accept order.', 'error')
    return redirect(url_for('driver.available_orders'))

@bp.route('/update-order-status/<order_id>', methods=['POST'])
@login_required
@driver_required
def update_order_status(order_id):
    try:
        # Get JSON data
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        status = data['status']
        message = data.get('message', '')
        
        # Verify the order belongs to this driver
        order = order_service.get_order_by_id(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
            
        if order.driver_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Update the order status
        update = order_service.update_order_status(
            order_id=order_id,
            status=status,
            driver_id=current_user.id,
            message=message
        )
        
        if update:
            return jsonify({
                'message': 'Order status updated successfully',
                'status': status
            }), 200
        else:
            return jsonify({'error': 'Failed to update order status'}), 400
            
    except Exception as e:
        print(f"Error updating order status: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/deliveries/<order_id>')
@login_required
@driver_required
def view_delivery(order_id):
    order = order_service.get_order_by_id(order_id)
    
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('driver.my_deliveries'))
    
    # Ensure drivers can only view their assigned orders
    if order.driver_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('driver.my_deliveries'))
        
    return render_template('driver/delivery_details.html', order=order)

@bp.route('/create-ticket', methods=['POST'])
@login_required
@driver_required
def create_ticket():
    subject = request.form.get('subject')
    description = request.form.get('description')
    order_id = request.form.get('order_id')
    
    if not subject or not description:
        flash('Subject and description are required', 'error')
        return redirect(url_for('driver.tickets'))
    
    try:
        ticket = ticket_service.create_driver_ticket(
            driver_id=current_user.id,
            subject=subject,
            description=description,
            order_id=order_id if order_id else None
        )
        
        if ticket:
            flash('Ticket created successfully', 'success')
            return redirect(url_for('driver.view_ticket', ticket_id=ticket.id))
        else:
            flash('Failed to create ticket', 'error')
            
    except Exception as e:
        print(f"Error creating ticket: {e}")
        flash('An error occurred while creating the ticket', 'error')
    
    return redirect(url_for('driver.tickets')) 