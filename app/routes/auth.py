from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from ..services.auth_service import AuthService
from functools import wraps
import jwt
from ..config import Config
from flask_login import login_user, logout_user, login_required, current_user

bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_service = AuthService()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = auth_service.get_user_by_id(data['user_id'])
            return f(current_user, *args, **kwargs)
        except:
            return jsonify({'message': 'Token is invalid'}), 401
    return decorated

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        user_type = request.form.get('user_type', 'user')  # Default to regular user
        
        user, error = auth_service.register_user(
            email=email,
            password=password,
            user_type=user_type,
            full_name=full_name,
            phone_number=phone_number
        )
        
        if user:
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('auth.login'))
        
        flash(error or 'Registration failed.', 'error')
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_user_by_type(current_user)
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = auth_service.login(email, password)
        if user:
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect_user_by_type(user)
        
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html')

def redirect_user_by_type(user):
    """Helper function to redirect users based on their type"""
    if user.user_type == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif user.user_type == 'driver':
        return redirect(url_for('driver.dashboard'))
    else:
        return redirect(url_for('user.dashboard'))

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login')) 