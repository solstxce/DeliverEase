from functools import wraps
from flask import request, jsonify, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.user_type == 'admin':
            flash('Admin privileges required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def driver_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.user_type == 'driver':
            flash('Driver privileges required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def user_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.user_type == 'user':
            flash('User privileges required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated 