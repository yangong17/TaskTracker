"""
Configuration settings for the TaskTracker application.

Provides different configuration classes for different environments
to ensure proper separation of concerns and security.
"""

import os
from typing import Dict, Any


class Config:
    """Base configuration class with common settings."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Application settings
    APP_NAME = "TaskTracker"
    APP_VERSION = "2.0.0"
    
    # File storage settings
    LOG_FILENAME = "task_log.csv"
    FAVORITES_FILENAME = "favorites.csv"
    
    # Pomodoro timer defaults
    DEFAULT_WORK_MINUTES = 25
    DEFAULT_REST_MINUTES = 5
    
    # Task management settings
    DEFAULT_PRIORITY = 3
    MAX_PRIORITY = 5
    MIN_PRIORITY = 1
    
    # Timer settings
    TIMER_UPDATE_INTERVAL = 1  # seconds
    LOW_TIME_THRESHOLD = 900   # 15 minutes in seconds
    
    # UI settings
    TIME_INCREMENTS_COUNT = 48  # 12 hours in 15-minute increments
    TIME_INCREMENT_MINUTES = 15
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration."""
        pass


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    
    # Enable detailed error pages
    EXPLAIN_TEMPLATE_LOADING = True
    
    # Development logging
    LOG_LEVEL = "DEBUG"
    
    @staticmethod
    def init_app(app):
        """Initialize development-specific settings."""
        Config.init_app(app)
        
        # Development-specific initialization
        import logging
        logging.basicConfig(level=logging.DEBUG)


class ProductionConfig(Config):
    """Production environment configuration."""
    
    DEBUG = False
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Production logging
    LOG_LEVEL = "INFO"
    
    @staticmethod
    def init_app(app):
        """Initialize production-specific settings."""
        Config.init_app(app)
        
        # Production logging setup
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            # Create logs directory if it doesn't exist
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            # Configure rotating file handler
            file_handler = RotatingFileHandler(
                'logs/tasktracker.log',
                maxBytes=10240,
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('TaskTracker startup')


class TestingConfig(Config):
    """Testing environment configuration."""
    
    TESTING = True
    DEBUG = True
    
    # Test-specific settings
    WTF_CSRF_ENABLED = False
    LOG_FILENAME = "test_task_log.csv"
    FAVORITES_FILENAME = "test_favorites.csv"
    
    @staticmethod
    def init_app(app):
        """Initialize testing-specific settings."""
        Config.init_app(app)


# Configuration mapping
config: Dict[str, Any] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 