from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from ..services.ticket_service import TicketService
from flask_login import login_required, current_user

bp = Blueprint('ticket', __name__, url_prefix='/tickets')
ticket_service = TicketService()

@bp.route('/<ticket_id>')
@login_required
def ticket_detail(ticket_id):
    ticket = ticket_service.get_ticket(ticket_id)
    
    # Check if ticket exists
    if not ticket:
        flash('Ticket not found', 'error')
        return redirect(url_for('user.tickets'))
    
    # Check permissions using dictionary access instead of attribute access
    if ticket['user']['id'] != current_user.id and current_user.user_type != 'admin':
        flash('You do not have permission to view this ticket', 'error')
        return redirect(url_for('user.tickets'))
    
    # No need to get messages separately as they're already included in the ticket
    return render_template('tickets/detail.html', ticket=ticket)

@bp.route('/<ticket_id>/messages', methods=['POST'])
@login_required
def add_message(ticket_id):
    try:
        message = ticket_service.add_message(
            ticket_id=ticket_id,
            sender_id=current_user.id,
            message=request.form.get('message')
        )
        flash('Message sent successfully', 'success')
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('ticket.ticket_detail', ticket_id=ticket_id))

@bp.route('/<ticket_id>/close', methods=['POST'])
@login_required
def close_ticket(ticket_id):
    ticket = ticket_service.get_ticket(ticket_id)
    
    # Check if ticket exists
    if not ticket:
        flash('Ticket not found', 'error')
        return redirect(url_for('user.tickets'))
    
    # Check permissions using dictionary access
    if ticket['user']['id'] != current_user.id and current_user.user_type != 'admin':
        flash('You do not have permission to close this ticket', 'error')
        return redirect(url_for('user.tickets'))
    
    try:
        ticket_service.close_ticket(ticket_id)
        flash('Ticket closed successfully', 'success')
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('user.tickets')) 