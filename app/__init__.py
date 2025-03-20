from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager

login_manager = LoginManager()

def create_app(config):
    # Create Flask app instance
    app = Flask(__name__,
                template_folder='../frontend/templates',  # Set custom template folder
                static_folder='../frontend/static')       # Set custom static folder
    
    # Configure app
    app.config.from_object(config)
    
    # Enable CORS
    CORS(app)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Register blueprints
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.user import bp as user_bp
    from app.routes.driver import bp as driver_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.ticket import bp as ticket_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ticket_bp)
    
    return app

# Add this to handle user loading
@login_manager.user_loader
def load_user(user_id):
    from .services.auth_service import AuthService
    auth_service = AuthService()
    return auth_service.get_user_by_id(user_id) 