"""
Pomodoro service for the TaskTracker application.

Provides business logic for Pomodoro timer sessions with proper
state management, session transitions, and configuration.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from ..models.pomodoro import PomodoroSession, SessionType, SessionState

logger = logging.getLogger(__name__)


class PomodoroService:
    """Service class for managing Pomodoro timer sessions."""
    
    def __init__(self, work_minutes: int = 25, rest_minutes: int = 5):
        """
        Initialize the Pomodoro service.
        
        Args:
            work_minutes: Default duration for work sessions
            rest_minutes: Default duration for rest sessions
        """
        self._session = PomodoroSession(
            work_minutes=work_minutes,
            rest_minutes=rest_minutes,
            duration_minutes=work_minutes  # Start with work session
        )
        
        logger.info(f"Initialized Pomodoro service: work={work_minutes}min, rest={rest_minutes}min")
    
    def toggle_focus_mode(self) -> bool:
        """
        Toggle focus mode on/off.
        
        Returns:
            True if focus mode is now enabled
        """
        self._session.toggle_focus_mode()
        return self._session.is_focus_mode
    
    def is_focus_mode_active(self) -> bool:
        """Check if focus mode is currently active."""
        return self._session.is_focus_mode
    
    def update_settings(self, work_minutes: int, rest_minutes: int) -> bool:
        """
        Update Pomodoro timer settings.
        
        Args:
            work_minutes: Duration for work sessions
            rest_minutes: Duration for rest sessions
            
        Returns:
            True if settings were updated successfully
        """
        try:
            self._session.update_settings(work_minutes, rest_minutes)
            logger.info(f"Updated Pomodoro settings: work={work_minutes}min, rest={rest_minutes}min")
            return True
        except ValueError as e:
            logger.error(f"Failed to update settings: {e}")
            return False
    
    def start_session(self) -> bool:
        """
        Start the current Pomodoro session.
        
        Returns:
            True if session was started successfully
        """
        try:
            self._session.start_session()
            return True
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return False
    
    def pause_session(self) -> bool:
        """
        Pause the current session.
        
        Returns:
            True if session was paused successfully
        """
        try:
            self._session.pause_session()
            return True
        except Exception as e:
            logger.error(f"Failed to pause session: {e}")
            return False
    
    def resume_session(self) -> bool:
        """
        Resume a paused session.
        
        Returns:
            True if session was resumed successfully
        """
        try:
            self._session.resume_session()
            return True
        except Exception as e:
            logger.error(f"Failed to resume session: {e}")
            return False
    
    def reset_session(self) -> bool:
        """
        Reset the Pomodoro session to initial state.
        
        Returns:
            True if session was reset successfully
        """
        try:
            self._session.reset_session()
            return True
        except Exception as e:
            logger.error(f"Failed to reset session: {e}")
            return False
    
    def get_session_data(self) -> Dict[str, Any]:
        """
        Get current session data for API responses.
        
        Returns:
            Dictionary with current session information
        """
        # Check for session completion and handle transitions
        session_changed = False
        if self._session.is_session_complete() and self._session.state == SessionState.RUNNING:
            previous_type = self._session.session_type
            session_changed = self._session.complete_session()
            
            if session_changed:
                logger.info(f"Session transition: {previous_type.value} -> {self._session.session_type.value}")
        
        data = self._session.to_dict()
        data['session_changed'] = session_changed
        
        # Add transition information if session changed
        if session_changed:
            data['previous_session_was_work'] = data['session_type'] != 'work'
        
        return data
    
    def get_work_minutes(self) -> int:
        """Get current work session duration."""
        return self._session.work_minutes
    
    def get_rest_minutes(self) -> int:
        """Get current rest session duration."""
        return self._session.rest_minutes
    
    def get_current_session_type(self) -> SessionType:
        """Get the current session type."""
        return self._session.session_type
    
    def get_session_state(self) -> SessionState:
        """Get the current session state."""
        return self._session.state
    
    def is_session_running(self) -> bool:
        """Check if a session is currently running."""
        return self._session.state == SessionState.RUNNING
    
    def is_session_paused(self) -> bool:
        """Check if a session is currently paused."""
        return self._session.state == SessionState.PAUSED
    
    def get_work_sessions_completed(self) -> int:
        """Get number of completed work sessions."""
        return self._session.work_sessions_completed
    
    def get_rest_sessions_completed(self) -> int:
        """Get number of completed rest sessions."""
        return self._session.rest_sessions_completed
    
    def get_remaining_seconds(self) -> int:
        """Get remaining seconds in current session."""
        return self._session.get_remaining_seconds()
    
    def get_session_progress(self) -> float:
        """
        Get session progress as a percentage.
        
        Returns:
            Progress from 0.0 to 1.0
        """
        total_seconds = self._session.duration_minutes * 60
        remaining_seconds = self._session.get_remaining_seconds()
        
        if total_seconds <= 0:
            return 1.0
        
        progress = 1.0 - (remaining_seconds / total_seconds)
        return max(0.0, min(1.0, progress))  # Clamp between 0 and 1
    
    def get_formatted_time_remaining(self) -> str:
        """
        Get formatted time remaining (MM:SS).
        
        Returns:
            Formatted time string
        """
        remaining = self._session.get_remaining_seconds()
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current Pomodoro session.
        
        Returns:
            Dictionary with session summary information
        """
        return {
            'focus_mode_active': self._session.is_focus_mode,
            'session_type': self._session.session_type.value,
            'session_state': self._session.state.value,
            'time_remaining': self.get_formatted_time_remaining(),
            'progress': self.get_session_progress(),
            'work_sessions_completed': self._session.work_sessions_completed,
            'rest_sessions_completed': self._session.rest_sessions_completed,
            'work_duration': self._session.work_minutes,
            'rest_duration': self._session.rest_minutes,
            'total_sessions': (
                self._session.work_sessions_completed + 
                self._session.rest_sessions_completed
            )
        }
    
    def handle_manual_session_change(self, to_work_session: bool) -> bool:
        """
        Manually change session type (for testing or manual control).
        
        Args:
            to_work_session: True to switch to work session, False for rest
            
        Returns:
            True if session was changed successfully
        """
        try:
            if to_work_session:
                self._session.session_type = SessionType.WORK
                self._session.duration_minutes = self._session.work_minutes
            else:
                self._session.session_type = SessionType.REST
                self._session.duration_minutes = self._session.rest_minutes
            
            # Reset timing if session is running
            if self._session.state == SessionState.RUNNING:
                self._session.start_time = datetime.now()
                self._session.paused_elapsed = 0.0
            
            logger.info(f"Manually changed to {self._session.session_type.value} session")
            return True
            
        except Exception as e:
            logger.error(f"Failed to change session type: {e}")
            return False
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get detailed session statistics.
        
        Returns:
            Dictionary with detailed statistics
        """
        total_work_time = self._session.work_sessions_completed * self._session.work_minutes
        total_rest_time = self._session.rest_sessions_completed * self._session.rest_minutes
        total_time = total_work_time + total_rest_time
        
        productivity_ratio = (
            (total_work_time / total_time * 100) if total_time > 0 else 0
        )
        
        return {
            'work_sessions': self._session.work_sessions_completed,
            'rest_sessions': self._session.rest_sessions_completed,
            'total_sessions': (
                self._session.work_sessions_completed + 
                self._session.rest_sessions_completed
            ),
            'total_work_minutes': total_work_time,
            'total_rest_minutes': total_rest_time,
            'total_minutes': total_time,
            'productivity_ratio': round(productivity_ratio, 1),
            'average_session_length': (
                (self._session.work_minutes + self._session.rest_minutes) / 2
            ),
            'current_streak': self._calculate_current_streak()
        }
    
    def _calculate_current_streak(self) -> int:
        """
        Calculate the current streak of completed sessions.
        
        Returns:
            Number of consecutive completed sessions
        """
        # For now, return total sessions as a simple streak
        # This could be enhanced to track actual consecutive completions
        return (
            self._session.work_sessions_completed + 
            self._session.rest_sessions_completed
        ) 