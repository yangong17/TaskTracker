"""
TaskTracker - A professional task management application with Pomodoro timer.

This package contains a modular Flask application designed for high reliability
and maintainability, critical for project managers in developing nations.
"""

__version__ = "2.0.0"
__author__ = "TaskTracker Development Team"

from .app import create_app

__all__ = ["create_app"] 