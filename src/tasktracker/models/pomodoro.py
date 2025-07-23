"""
Pomodoro session model for the TaskTracker application.

Provides a robust model for managing Pomodoro timer sessions
with proper state management and validation.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SessionType(Enum):
    """Enumeration for different session types."""
    WORK = "work"
    REST = "rest"


class SessionState(Enum):
    """Enumeration for session states."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class PomodoroSession:
    """
    Represents a Pomodoro session in the TaskTracker system.
    
    Attributes:
        session_type: Type of session (work or rest)
        duration_minutes: Duration of the session in minutes
        work_sessions_completed: Number of completed work sessions
        rest_sessions_completed: Number of completed rest sessions
        state: Current state of the session
        start_time: When the session was started
        paused_elapsed: Time elapsed when paused
        is_focus_mode: Whether focus mode is active
    """
    
    session_type: SessionType = SessionType.WORK
    duration_minutes: int = 25
    work_sessions_completed: int = 0
    rest_sessions_completed: int = 0
    state: SessionState = SessionState.NOT_STARTED
    start_time: Optional[datetime] = None
    paused_elapsed: float = 0.0
    is_focus_mode: bool = False
    
    # Configuration
    work_minutes: int = 25
    rest_minutes: int = 5
    
    def __post_init__(self):
        """Validate session data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate session data.
        
        Raises:
            ValueError: If session data is invalid
        """
        if self.duration_minutes <= 0:
            raise ValueError("Duration must be positive")
        
        if self.work_minutes <= 0 or self.rest_minutes <= 0:
            raise ValueError("Work and rest minutes must be positive")
        
        if self.paused_elapsed < 0:
            raise ValueError("Paused elapsed time cannot be negative")
    
    def start_session(self) -> None:
        """Start the current session."""
        if self.state == SessionState.RUNNING:
            logger.warning("Session is already running")
            return
        
        self.state = SessionState.RUNNING
        self.start_time = datetime.now()
        self.paused_elapsed = 0.0
        
        logger.info(f"Started {self.session_type.value} session")
    
    def pause_session(self) -> None:
        """Pause the current session."""
        if self.state != SessionState.RUNNING:
            logger.warning("Cannot pause session that is not running")
            return
        
        if self.start_time:
            self.paused_elapsed = (datetime.now() - self.start_time).total_seconds()
        
        self.state = SessionState.PAUSED
        logger.info(f"Paused {self.session_type.value} session")
    
    def resume_session(self) -> None:
        """Resume a paused session."""
        if self.state != SessionState.PAUSED:
            logger.warning("Cannot resume session that is not paused")
            return
        
        self.start_time = datetime.now() - timedelta(seconds=self.paused_elapsed)
        self.state = SessionState.RUNNING
        self.paused_elapsed = 0.0
        
        logger.info(f"Resumed {self.session_type.value} session")
    
    def reset_session(self) -> None:
        """Reset the session to initial state."""
        self.state = SessionState.NOT_STARTED
        self.start_time = None
        self.paused_elapsed = 0.0
        self.session_type = SessionType.WORK
        self.work_sessions_completed = 0
        self.rest_sessions_completed = 0
        
        logger.info("Reset Pomodoro session")
    
    def get_remaining_seconds(self) -> int:
        """
        Get remaining seconds in the current session.
        
        Returns:
            Remaining seconds (0 if session is complete)
        """
        if not self.start_time:
            return self.duration_minutes * 60
        
        if self.state == SessionState.PAUSED:
            elapsed_seconds = self.paused_elapsed
        elif self.state == SessionState.RUNNING:
            elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        else:
            return self.duration_minutes * 60
        
        total_duration = self.duration_minutes * 60
        remaining = max(0, total_duration - elapsed_seconds)
        
        return int(remaining)
    
    def is_session_complete(self) -> bool:
        """Check if the current session is complete."""
        return self.get_remaining_seconds() <= 0 and self.state == SessionState.RUNNING
    
    def complete_session(self) -> bool:
        """
        Complete the current session and transition to next.
        
        Returns:
            True if session was completed and transitioned
        """
        if not self.is_session_complete():
            return False
        
        self.state = SessionState.COMPLETED
        
        # Update completion counters
        if self.session_type == SessionType.WORK:
            self.work_sessions_completed += 1
            next_session = SessionType.REST
            next_duration = self.rest_minutes
        else:
            self.rest_sessions_completed += 1
            next_session = SessionType.WORK
            next_duration = self.work_minutes
        
        logger.info(f"Completed {self.session_type.value} session")
        
        # Transition to next session
        self.session_type = next_session
        self.duration_minutes = next_duration
        self.start_time = datetime.now()
        self.state = SessionState.RUNNING
        self.paused_elapsed = 0.0
        
        logger.info(f"Transitioned to {self.session_type.value} session")
        
        return True
    
    def update_settings(self, work_minutes: int, rest_minutes: int) -> None:
        """
        Update session duration settings.
        
        Args:
            work_minutes: Duration for work sessions
            rest_minutes: Duration for rest sessions
        """
        if work_minutes <= 0 or rest_minutes <= 0:
            raise ValueError("Work and rest minutes must be positive")
        
        self.work_minutes = work_minutes
        self.rest_minutes = rest_minutes
        
        # Update current session duration if it matches the type
        if self.session_type == SessionType.WORK:
            self.duration_minutes = work_minutes
        else:
            self.duration_minutes = rest_minutes
        
        logger.info(f"Updated settings: work={work_minutes}min, rest={rest_minutes}min")
    
    def toggle_focus_mode(self) -> None:
        """Toggle focus mode on/off."""
        self.is_focus_mode = not self.is_focus_mode
        
        if not self.is_focus_mode:
            self.reset_session()
        
        logger.info(f"Focus mode {'enabled' if self.is_focus_mode else 'disabled'}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the session
        """
        return {
            'remaining_seconds': self.get_remaining_seconds(),
            'is_work_session': self.session_type == SessionType.WORK,
            'is_running': self.state == SessionState.RUNNING,
            'is_paused': self.state == SessionState.PAUSED,
            'session_complete': self.is_session_complete(),
            'session_changed': False,  # This will be set by the service layer
            'work_sessions_completed': self.work_sessions_completed,
            'rest_sessions_completed': self.rest_sessions_completed,
            'duration_minutes': self.duration_minutes,
            'work_minutes': self.work_minutes,
            'rest_minutes': self.rest_minutes,
            'is_focus_mode': self.is_focus_mode,
            'state': self.state.value,
            'session_type': self.session_type.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PomodoroSession':
        """
        Create a PomodoroSession instance from a dictionary.
        
        Args:
            data: Dictionary containing session data
            
        Returns:
            PomodoroSession instance
        """
        session = cls(
            session_type=SessionType(data.get('session_type', 'work')),
            duration_minutes=data.get('duration_minutes', 25),
            work_sessions_completed=data.get('work_sessions_completed', 0),
            rest_sessions_completed=data.get('rest_sessions_completed', 0),
            state=SessionState(data.get('state', 'not_started')),
            paused_elapsed=data.get('paused_elapsed', 0.0),
            is_focus_mode=data.get('is_focus_mode', False),
            work_minutes=data.get('work_minutes', 25),
            rest_minutes=data.get('rest_minutes', 5)
        )
        
        # Parse start_time if present
        if data.get('start_time'):
            session.start_time = datetime.fromisoformat(data['start_time'])
        
        return session
    
    def __str__(self) -> str:
        """String representation of the session."""
        remaining = self.get_remaining_seconds()
        minutes = remaining // 60
        seconds = remaining % 60
        
        return (
            f"{self.session_type.value.title()} Session - "
            f"{minutes:02d}:{seconds:02d} - "
            f"{self.state.value.title()}"
        )
    
    def __repr__(self) -> str:
        """Developer representation of the session."""
        return (
            f"PomodoroSession(type={self.session_type.value}, "
            f"duration={self.duration_minutes}min, state={self.state.value})"
        ) 