from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from ..services.order_service import OrderService
from ..services.ticket_service import TicketService
from flask_login import login_required, current_user
from ..utils.decorators import user_required

bp = Blueprint('user', __name__, url_prefix='/user')
order_service = OrderService()
ticket_service = TicketService()

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type != 'user':
        return redirect_user_by_type(current_user)
    orders = order_service.get_user_orders(current_user.id)
    return render_template('user/dashboard.html', orders=orders)

@bp.route('/create-order', methods=['GET', 'POST'])
@login_required
@user_required
def create_order():
    if request.method == 'POST':
        order = order_service.create_order(
            user_id=current_user.id,
            pickup_location=request.form.get('pickup_location'),
            delivery_location=request.form.get('delivery_location'),
            item_description=request.form.get('item_description'),
            weight=float(request.form.get('weight')),
            price=float(request.form.get('price'))
        )
        
        if order:
            flash('Order created successfully.', 'success')
            return redirect(url_for('user.orders'))
        flash('Failed to create order.', 'error')
    
    return render_template('user/create_order.html')

@bp.route('/orders')
@login_required
@user_required
def orders():
    orders = order_service.get_user_orders(current_user.id)
    return render_template('user/orders.html', orders=orders)

@bp.route('/tickets')
@login_required
@user_required
def tickets():
    tickets = ticket_service.get_user_tickets(current_user.id)
    return render_template('user/tickets.html', tickets=tickets)

@bp.route('/create-ticket', methods=['GET', 'POST'])
@login_required
@user_required
def create_ticket():
    if request.method == 'POST':
        ticket = ticket_service.create_ticket(
            user_id=current_user.id,
            subject=request.form.get('subject'),
            message=request.form.get('message')
        )
        
        if ticket:
            flash('Support ticket created successfully.', 'success')
            return redirect(url_for('user.tickets'))
        flash('Failed to create ticket.', 'error')
    
    return render_template('user/create_ticket.html')

@bp.route('/tickets/<ticket_id>/messages', methods=['POST'])
@login_required
@user_required
def add_ticket_message(ticket_id):
    try:
        # Get form data instead of JSON
        message = request.form.get('message')
        if not message:
            return jsonify({'error': 'Message is required'}), 400

        ticket_message = ticket_service.add_message(
            ticket_id=ticket_id,
            sender_id=current_user.id,
            message=message
        )
        
        if ticket_message:
            return jsonify({'message': 'Message added successfully'}), 201
        return jsonify({'error': 'Failed to add message'}), 400
    except Exception as e:
        print(f"Error adding message: {e}")
        return jsonify({'error': str(e)}), 400

@bp.route('/orders/<order_id>')
@login_required
def view_order(order_id):
    order_service = OrderService()
    order = order_service.get_order_by_id(order_id)
    
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('user.orders'))
    
    # Ensure users can only view their own orders
    if order.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('user.orders'))
        
    return render_template('user/order_details.html', order=order)

@bp.route('/view_ticket/<ticket_id>')
@login_required
@user_required
def view_ticket(ticket_id):
    try:
        ticket = ticket_service.get_ticket_by_id(ticket_id)
        
        if not ticket:
            flash('Ticket not found', 'error')
            return redirect(url_for('user.tickets'))
        
        # Ensure users can only view their own tickets
        if ticket.user_id != current_user.id:
            flash('Access denied', 'error')
            return redirect(url_for('user.tickets'))
            
        return render_template('user/ticket_details.html', ticket=ticket)
    except Exception as e:
        print(f"Error viewing ticket: {e}")
        flash('An error occurred while retrieving ticket details', 'error')
        return redirect(url_for('user.tickets')) 