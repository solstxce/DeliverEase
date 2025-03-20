import os
from app import create_app
from app.config import Config

# Determine environment
env = os.environ.get('FLASK_ENV', 'development')
config = Config

# Create app instance
app = create_app(config)

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(
        host='0.0.0.0',  # Make server publicly available
        port=port,
        debug=env == 'development'  # Enable debug mode in development
    ) 