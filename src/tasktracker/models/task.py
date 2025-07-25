"""
Task model for the TaskTracker application.

Provides a robust data model for task management with validation,
priority handling, and deadline management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """
    Represents a task in the TaskTracker system.
    
    Attributes:
        text: The task description
        completed: Whether the task is completed
        priority: Task priority (1=highest, 5=lowest)
        task_deadline: Optional deadline for the task
        lap_time: Time taken to complete the task (formatted string)
        created_at: When the task was created
        completed_at: When the task was completed
    """
    
    text: str
    completed: bool = False
    priority: int = 3
    task_deadline: Optional[datetime] = None
    lap_time: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate task data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate task data.
        
        Raises:
            ValueError: If task data is invalid
        """
        if not self.text or not self.text.strip():
            raise ValueError("Task text cannot be empty")
        
        if not isinstance(self.priority, int) or not (1 <= self.priority <= 5):
            raise ValueError("Priority must be an integer between 1 and 5")
        
        if self.task_deadline and self.task_deadline < datetime.now():
            logger.warning(f"Task '{self.text}' has a deadline in the past")
    
    def mark_completed(self, lap_seconds: Optional[int] = None) -> None:
        """
        Mark the task as completed.
        
        Args:
            lap_seconds: Time taken to complete the task in seconds
        """
        if self.completed:
            logger.warning(f"Task '{self.text}' is already completed")
            return
        
        self.completed = True
        self.completed_at = datetime.now()
        
        if lap_seconds is not None:
            self.lap_time = self._format_lap_time(lap_seconds)
        
        logger.info(f"Task '{self.text}' marked as completed")
    
    def mark_incomplete(self) -> None:
        """Mark the task as incomplete."""
        if not self.completed:
            logger.warning(f"Task '{self.text}' is already incomplete")
            return
        
        self.completed = False
        self.completed_at = None
        self.lap_time = None
        
        logger.info(f"Task '{self.text}' marked as incomplete")
    
    def is_overdue(self) -> bool:
        """
        Check if the task is overdue.
        
        Returns:
            True if task has a deadline and it's in the past
        """
        return (
            self.task_deadline is not None and 
            not self.completed and 
            datetime.now() > self.task_deadline
        )
    
    def time_until_deadline(self) -> Optional[timedelta]:
        """
        Get time remaining until deadline.
        
        Returns:
            Time remaining as timedelta, or None if no deadline
        """
        if not self.task_deadline:
            return None
        
        return self.task_deadline - datetime.now()
    
    def get_priority_color(self) -> str:
        """
        Get the color associated with the task's priority.
        
        Returns:
            Hex color code for the priority level
        """
        priority_colors = {
            1: '#dc3545',  # Red - highest priority
            2: '#fd7e14',  # Orange
            3: '#ffc107',  # Yellow
            4: '#20c997',  # Teal
            5: '#28a745',  # Green - lowest priority
        }
        return priority_colors.get(self.priority, '#6c757d')  # Gray as fallback
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            'text': self.text,
            'completed': self.completed,
            'priority': self.priority,
            'task_deadline': self.task_deadline.isoformat() if self.task_deadline else None,
            'lap_time': self.lap_time,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        # Parse datetime strings
        task_deadline = datetime.fromisoformat(data['task_deadline']) if data.get('task_deadline') else None
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        completed_at = datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        
        return cls(
            text=data['text'],
            completed=data.get('completed', False),
            priority=data.get('priority', 3),
            task_deadline=task_deadline,
            lap_time=data.get('lap_time'),
            created_at=created_at,
            completed_at=completed_at
        )
    
    @staticmethod
    def _format_lap_time(seconds: int) -> str:
        """
        Format lap time in a human-readable format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string (e.g., "1h 30m 45s" or "5m 30s")
        """
        if seconds < 60:
            return f"{seconds}s"
        
        hours = seconds // 3600
        remaining_seconds = seconds % 3600
        minutes = remaining_seconds // 60
        secs = remaining_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        else:
            return f"{minutes}m {secs}s"
    
    def __str__(self) -> str:
        """String representation of the task."""
        status = "✓" if self.completed else "○"
        deadline = f" (due: {self.task_deadline.strftime('%m/%d %H:%M')})" if self.task_deadline else ""
        return f"{status} [{self.priority}] {self.text}{deadline}"
    
    def __repr__(self) -> str:
        """Developer representation of the task."""
        return (
            f"Task(text='{self.text}', completed={self.completed}, "
            f"priority={self.priority}, deadline={self.task_deadline})"
        ) 