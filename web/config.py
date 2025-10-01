"""
Web application configuration
"""

import os
from pathlib import Path

class WebConfig:
    """Web application configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ultra-turbo-cleaner-dev-key-2025'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # WebSocket settings
    SOCKETIO_ASYNC_MODE = 'threading'
    
    # Static files
    STATIC_FOLDER = 'static'
    TEMPLATE_FOLDER = 'templates'
    
    # Application paths
    BASE_DIR = Path(__file__).parent
    PROJECT_ROOT = BASE_DIR.parent
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def init_app(app):
        """Initialize Flask app with configuration"""
        app.config.from_object(WebConfig)
        
        # Additional security headers
        @app.after_request
        def security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            return response

class DevelopmentConfig(WebConfig):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(WebConfig):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(WebConfig):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}