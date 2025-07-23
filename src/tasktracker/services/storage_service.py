"""
Storage service for the TaskTracker application.

Handles all data persistence operations including CSV file management,
task logs, and favorites with proper error handling and data integrity.
"""

import csv
import os
import json
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StorageService:
    """Service class for handling data storage and retrieval."""
    
    def __init__(self, log_filename: str = "task_log.csv", 
                 favorites_filename: str = "favorites.csv",
                 tasks_filename: str = "tasks.json"):
        """
        Initialize the storage service.
        
        Args:
            log_filename: Filename for task completion log
            favorites_filename: Filename for favorites
            tasks_filename: Filename for task data
        """
        self.log_filename = log_filename
        self.favorites_filename = favorites_filename
        self.tasks_filename = tasks_filename
        
        # Initialize storage files
        self._ensure_files_exist()
        
        # Load data
        self._task_log: Dict[str, Dict[str, Any]] = {}
        self._favorites: List[str] = []
        
        self._load_all_data()
    
    def _ensure_files_exist(self) -> None:
        """Ensure all storage files exist."""
        files_to_create = [
            (self.log_filename, self._create_empty_csv),
            (self.favorites_filename, self._create_empty_csv),
            (self.tasks_filename, self._create_empty_json)
        ]
        
        for filename, creator_func in files_to_create:
            if not os.path.exists(filename):
                try:
                    creator_func(filename)
                    logger.info(f"Created storage file: {filename}")
                except Exception as e:
                    logger.error(f"Failed to create {filename}: {e}")
    
    def _create_empty_csv(self, filename: str) -> None:
        """Create an empty CSV file."""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            pass  # Create empty file
    
    def _create_empty_json(self, filename: str) -> None:
        """Create an empty JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    def _load_all_data(self) -> None:
        """Load all data from storage files."""
        self._load_task_log()
        self._load_favorites()
    
    def _load_task_log(self) -> None:
        """Load the task completion log from CSV."""
        self._task_log = {}
        
        if not os.path.exists(self.log_filename):
            return
        
        try:
            with open(self.log_filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        task_name, fastest_str = row[0], row[1]
                        try:
                            fastest_time = int(fastest_str)
                            self._task_log[task_name] = {"fastest_time": fastest_time}
                        except ValueError:
                            logger.warning(f"Invalid fastest time for task '{task_name}': {fastest_str}")
            
            # Sort alphabetically
            self._task_log = dict(sorted(self._task_log.items()))
            logger.info(f"Loaded {len(self._task_log)} task log entries")
            
        except Exception as e:
            logger.error(f"Failed to load task log: {e}")
            self._task_log = {}
    
    def _save_task_log(self) -> None:
        """Save the task completion log to CSV."""
        try:
            with open(self.log_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for name, data in self._task_log.items():
                    writer.writerow([name, data["fastest_time"]])
            
            logger.debug(f"Saved {len(self._task_log)} task log entries")
            
        except Exception as e:
            logger.error(f"Failed to save task log: {e}")
    
    def _load_favorites(self) -> None:
        """Load favorites from CSV."""
        self._favorites = []
        
        if not os.path.exists(self.favorites_filename):
            return
        
        try:
            with open(self.favorites_filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0]:  # Skip empty rows
                        self._favorites.append(row[0])
            
            logger.info(f"Loaded {len(self._favorites)} favorites")
            
        except Exception as e:
            logger.error(f"Failed to load favorites: {e}")
            self._favorites = []
    
    def _save_favorites(self) -> None:
        """Save favorites to CSV."""
        try:
            with open(self.favorites_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for favorite in self._favorites:
                    writer.writerow([favorite])
            
            logger.debug(f"Saved {len(self._favorites)} favorites")
            
        except Exception as e:
            logger.error(f"Failed to save favorites: {e}")
    
    # Task Log Operations
    def get_task_log(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the complete task log.
        
        Returns:
            Dictionary mapping task names to their data
        """
        return self._task_log.copy()
    
    def update_fastest_time(self, task_name: str, lap_seconds: int) -> bool:
        """
        Update the fastest time for a task.
        
        Args:
            task_name: Name of the task
            lap_seconds: Time taken in seconds
            
        Returns:
            True if this was a new record
        """
        if not task_name or lap_seconds < 0:
            logger.warning(f"Invalid task update: name='{task_name}', time={lap_seconds}")
            return False
        
        is_new_record = False
        
        if task_name not in self._task_log:
            # Brand new record
            self._task_log[task_name] = {"fastest_time": lap_seconds}
            is_new_record = True
            logger.info(f"New task record: {task_name} = {lap_seconds}s")
        else:
            # Check if it's faster
            current_fastest = self._task_log[task_name]["fastest_time"]
            if lap_seconds < current_fastest:
                self._task_log[task_name]["fastest_time"] = lap_seconds
                is_new_record = True
                logger.info(f"New fastest time for {task_name}: {lap_seconds}s (was {current_fastest}s)")
        
        # Re-sort and save
        self._task_log = dict(sorted(self._task_log.items()))
        self._save_task_log()
        
        return is_new_record
    
    def delete_task_from_log(self, task_name: str) -> bool:
        """
        Delete a task from the log.
        
        Args:
            task_name: Name of the task to delete
            
        Returns:
            True if task was deleted
        """
        if task_name in self._task_log:
            del self._task_log[task_name]
            self._save_task_log()
            logger.info(f"Deleted task from log: {task_name}")
            return True
        
        logger.warning(f"Task not found in log: {task_name}")
        return False
    
    # Favorites Operations
    def get_favorites(self) -> List[str]:
        """
        Get all favorites.
        
        Returns:
            List of favorite task names
        """
        return self._favorites.copy()
    
    def add_favorite(self, favorite_text: str) -> bool:
        """
        Add a new favorite.
        
        Args:
            favorite_text: Text to add as favorite
            
        Returns:
            True if added successfully, False if already exists
        """
        if not favorite_text or not favorite_text.strip():
            logger.warning("Cannot add empty favorite")
            return False
        
        favorite_text = favorite_text.strip()
        
        if favorite_text in self._favorites:
            logger.warning(f"Favorite already exists: {favorite_text}")
            return False
        
        self._favorites.append(favorite_text)
        self._save_favorites()
        logger.info(f"Added favorite: {favorite_text}")
        return True
    
    def delete_favorite(self, favorite_text: str) -> bool:
        """
        Delete a favorite.
        
        Args:
            favorite_text: Text to remove from favorites
            
        Returns:
            True if deleted successfully
        """
        if favorite_text in self._favorites:
            self._favorites.remove(favorite_text)
            self._save_favorites()
            logger.info(f"Deleted favorite: {favorite_text}")
            return True
        
        logger.warning(f"Favorite not found: {favorite_text}")
        return False
    
    # Task Data Operations (for future use with persistent task storage)
    def load_task_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        Load task data from JSON file.
        
        Returns:
            List of task dictionaries or None if file doesn't exist
        """
        if not os.path.exists(self.tasks_filename):
            return None
        
        try:
            with open(self.tasks_filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} tasks from {self.tasks_filename}")
                return data
        except Exception as e:
            logger.error(f"Failed to load task data: {e}")
            return None
    
    def save_task_data(self, tasks: List[Dict[str, Any]]) -> bool:
        """
        Save task data to JSON file.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            True if saved successfully
        """
        try:
            # Create backup if file exists
            if os.path.exists(self.tasks_filename):
                backup_name = f"{self.tasks_filename}.backup"
                os.rename(self.tasks_filename, backup_name)
            
            with open(self.tasks_filename, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=2, default=str)
            
            logger.debug(f"Saved {len(tasks)} tasks to {self.tasks_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save task data: {e}")
            
            # Restore backup if save failed
            backup_name = f"{self.tasks_filename}.backup"
            if os.path.exists(backup_name):
                os.rename(backup_name, self.tasks_filename)
                logger.info("Restored backup file after save failure")
            
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about storage files.
        
        Returns:
            Dictionary with storage file information
        """
        info = {}
        
        for filename, description in [
            (self.log_filename, "Task Log"),
            (self.favorites_filename, "Favorites"),
            (self.tasks_filename, "Tasks")
        ]:
            if os.path.exists(filename):
                stat = os.stat(filename)
                info[description] = {
                    "filename": filename,
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "exists": True
                }
            else:
                info[description] = {
                    "filename": filename,
                    "exists": False
                }
        
        return info 