"""
Task management service for the TaskTracker application.

Provides business logic for task operations, priority management,
and deadline handling with proper error handling and logging.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import logging

from ..models.task import Task
from .storage_service import StorageService

logger = logging.getLogger(__name__)


class TaskService:
    """Service class for managing tasks and task-related operations."""
    
    def __init__(self, storage_service: StorageService):
        """
        Initialize the task service.
        
        Args:
            storage_service: Service for data persistence
        """
        self.storage = storage_service
        self._tasks: List[Task] = []
        self._current_completion_time: Optional[datetime] = None
        self._spent_time_start: Optional[datetime] = None
        
        # Load existing tasks from storage
        self._load_tasks()
    
    def _load_tasks(self) -> None:
        """Load tasks from storage."""
        try:
            task_data = self.storage.load_task_data()
            if task_data:
                self._tasks = [Task.from_dict(data) for data in task_data]
                logger.info(f"Loaded {len(self._tasks)} tasks from storage")
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
            self._tasks = []
    
    def _save_tasks(self) -> None:
        """Save tasks to storage."""
        try:
            task_data = [task.to_dict() for task in self._tasks]
            self.storage.save_task_data(task_data)
            logger.debug(f"Saved {len(self._tasks)} tasks to storage")
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")
    
    def add_task(self, text: str, priority: int = 3, deadline: Optional[datetime] = None) -> Task:
        """
        Add a new task.
        
        Args:
            text: Task description
            priority: Task priority (1=highest, 5=lowest)
            deadline: Optional deadline for the task
            
        Returns:
            The created task
            
        Raises:
            ValueError: If task data is invalid
        """
        if not text or not text.strip():
            raise ValueError("Task text cannot be empty")
        
        task = Task(
            text=text.strip(),
            priority=priority,
            task_deadline=deadline
        )
        
        self._tasks.append(task)
        self._save_tasks()
        
        logger.info(f"Added task: {task}")
        return task
    
    def get_all_tasks(self) -> List[Task]:
        """
        Get all tasks.
        
        Returns:
            List of all tasks
        """
        return self._tasks.copy()
    
    def get_task(self, index: int) -> Optional[Task]:
        """
        Get a task by index.
        
        Args:
            index: Task index
            
        Returns:
            Task if found, None otherwise
        """
        if 0 <= index < len(self._tasks):
            return self._tasks[index]
        return None
    
    def update_task_priority(self, index: int, priority: int) -> bool:
        """
        Update a task's priority.
        
        Args:
            index: Task index
            priority: New priority (1-5)
            
        Returns:
            True if updated successfully
        """
        task = self.get_task(index)
        if not task:
            logger.warning(f"Task not found at index {index}")
            return False
        
        try:
            old_priority = task.priority
            task.priority = priority
            task.validate()  # Validate the new priority
            
            self._save_tasks()
            logger.info(f"Updated task priority from {old_priority} to {priority}: {task.text}")
            return True
            
        except ValueError as e:
            logger.error(f"Invalid priority {priority}: {e}")
            return False
    
    def update_task_deadline(self, index: int, deadline: Optional[datetime]) -> bool:
        """
        Update a task's deadline.
        
        Args:
            index: Task index
            deadline: New deadline (None to remove)
            
        Returns:
            True if updated successfully
        """
        task = self.get_task(index)
        if not task:
            logger.warning(f"Task not found at index {index}")
            return False
        
        old_deadline = task.task_deadline
        task.task_deadline = deadline
        
        self._save_tasks()
        logger.info(f"Updated task deadline from {old_deadline} to {deadline}: {task.text}")
        return True
    
    def complete_task(self, index: int) -> Tuple[bool, Optional[str]]:
        """
        Mark a task as completed and calculate lap time.
        
        Args:
            index: Task index
            
        Returns:
            Tuple of (success, lap_time_string)
        """
        task = self.get_task(index)
        if not task:
            logger.warning(f"Task not found at index {index}")
            return False, None
        
        if task.completed:
            # Unmark as completed
            task.mark_incomplete()
            self._save_tasks()
            return True, None
        
        # Calculate lap time
        lap_seconds = 0
        if self._current_completion_time:
            lap_seconds = int((datetime.now() - self._current_completion_time).total_seconds())
        
        # Mark as completed
        task.mark_completed(lap_seconds)
        
        # Update timing for next task
        self._current_completion_time = datetime.now()
        self._spent_time_start = datetime.now()
        
        # Update fastest time in log
        self.storage.update_fastest_time(task.text, lap_seconds)
        
        self._save_tasks()
        return True, task.lap_time
    
    def delete_task(self, index: int) -> bool:
        """
        Delete a task.
        
        Args:
            index: Task index
            
        Returns:
            True if deleted successfully
        """
        if 0 <= index < len(self._tasks):
            task = self._tasks.pop(index)
            self._save_tasks()
            logger.info(f"Deleted task: {task}")
            return True
        
        logger.warning(f"Task not found at index {index}")
        return False
    
    def clear_all_tasks(self) -> None:
        """Clear all tasks."""
        count = len(self._tasks)
        self._tasks.clear()
        self._save_tasks()
        logger.info(f"Cleared {count} tasks")
    
    def get_current_working_task(self) -> Optional[Task]:
        """
        Get the highest priority incomplete task.
        
        Returns:
            The current working task or None if no incomplete tasks
        """
        incomplete_tasks = [task for task in self._tasks if not task.completed]
        if not incomplete_tasks:
            return None
        
        # Sort by priority (lowest number = highest priority), then by creation time
        incomplete_tasks.sort(key=lambda t: (t.priority, t.created_at))
        return incomplete_tasks[0]
    
    def sort_tasks_by_priority(self, ascending: bool = True) -> None:
        """
        Sort tasks by priority.
        
        Args:
            ascending: If True, sort 1->5, if False, sort 5->1
        """
        self._tasks.sort(
            key=lambda t: (t.priority if ascending else -t.priority, t.created_at)
        )
        self._save_tasks()
        
        direction = "ascending" if ascending else "descending"
        logger.info(f"Sorted tasks by priority ({direction})")
    
    def sort_tasks_by_deadline(self) -> None:
        """Sort tasks by deadline (earliest first)."""
        def deadline_sort_key(task: Task) -> Tuple[datetime, int, datetime]:
            if task.task_deadline is None:
                # Tasks without deadlines go to the end
                return (datetime.max, task.priority, task.created_at)
            return (task.task_deadline, task.priority, task.created_at)
        
        self._tasks.sort(key=deadline_sort_key)
        self._save_tasks()
        logger.info("Sorted tasks by deadline")
    
    def get_overdue_tasks(self) -> List[Task]:
        """
        Get all overdue tasks.
        
        Returns:
            List of overdue tasks
        """
        return [task for task in self._tasks if task.is_overdue()]
    
    def get_tasks_by_priority(self, priority: int) -> List[Task]:
        """
        Get all tasks with a specific priority.
        
        Args:
            priority: Priority level (1-5)
            
        Returns:
            List of tasks with the specified priority
        """
        return [task for task in self._tasks if task.priority == priority]
    
    def get_completion_stats(self) -> Dict[str, Any]:
        """
        Get task completion statistics.
        
        Returns:
            Dictionary with completion statistics
        """
        total_tasks = len(self._tasks)
        completed_tasks = len([t for t in self._tasks if t.completed])
        overdue_tasks = len(self.get_overdue_tasks())
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'incomplete_tasks': total_tasks - completed_tasks,
            'overdue_tasks': overdue_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
    
    def set_completion_time(self, completion_time: datetime) -> None:
        """Set the last completion time for lap calculations."""
        self._current_completion_time = completion_time
    
    def set_spent_time_start(self, start_time: datetime) -> None:
        """Set the start time for spent time calculations."""
        self._spent_time_start = start_time
    
    def get_spent_time_seconds(self) -> int:
        """
        Get the time spent on current task in seconds.
        
        Returns:
            Time spent in seconds
        """
        if not self._spent_time_start:
            return 0
        
        return int((datetime.now() - self._spent_time_start).total_seconds())
    
    def is_all_done(self) -> bool:
        """
        Check if all tasks are completed.
        
        Returns:
            True if all tasks are completed
        """
        return len(self._tasks) > 0 and all(task.completed for task in self._tasks) 