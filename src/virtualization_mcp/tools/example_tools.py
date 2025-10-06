"""
Example Tools for VBoxMCP

This module provides example implementations of tools that demonstrate best practices
for creating tools in the VBoxMCP system. These tools can be used as templates for
creating new tools.

Key Features:
- Demonstrates proper tool structure and documentation
- Shows how to handle state within tools
- Includes examples of different parameter types
- Shows error handling patterns
- Demonstrates logging and monitoring
"""
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class Status(str, Enum):
    """Example status enum for demonstration purposes."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ExampleTools:
    """
    Example tools that demonstrate tool functionality and best practices.
    
    This class shows how to structure tools with proper state management,
    error handling, and documentation.
    """
    
    def __init__(self):
        """Initialize the example tools with default state."""
        self.counter = 0
        self.tasks: Dict[str, Dict] = {}
        logger.info("ExampleTools initialized")
    
    async def greet(self, name: str, title: Optional[str] = None) -> str:
        """Generate a greeting message.
        
        This is a simple example that shows how to handle optional parameters
        and return a string response.
        
        Args:
            name: The name of the person to greet
            title: Optional title (e.g., 'Dr.', 'Mr.', 'Ms.')
            
        Returns:
            A personalized greeting message
            
        Examples:
            >>> await greet("Alice")
            'Hello, Alice!'
            
            >>> await greet("Smith", title="Dr.")
            'Hello, Dr. Smith!'
        """
        if title:
            return f"Hello, {title} {name}!"
        return f"Hello, {name}!"
    
    async def create_task(self, description: str, priority: int = 1) -> Dict[str, str]:
        """Create a new task with the given description and priority.
        
        This example shows how to manage state within tools and return
        structured data.
        
        Args:
            description: Description of the task
            priority: Priority level (1-5, with 5 being highest)
            
        Returns:
            Dictionary containing task ID and status
            
        Raises:
            ValueError: If priority is not between 1 and 5
        """
        if not 1 <= priority <= 5:
            raise ValueError("Priority must be between 1 and 5")
            
        task_id = f"task_{len(self.tasks) + 1}"
        self.tasks[task_id] = {
            "id": task_id,
            "description": description,
            "priority": priority,
            "status": Status.PENDING,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Created task %s: %s", task_id, description)
        return {"id": task_id, "status": "created"}
    
    async def list_tasks(self, status: Optional[Status] = None) -> List[Dict]:
        """List all tasks, optionally filtered by status.
        
        Args:
            status: Optional status to filter tasks by
            
        Returns:
            List of task dictionaries
        """
        if status:
            return [task for task in self.tasks.values() if task["status"] == status]
        return list(self.tasks.values())
    
    async def get_counter(self, increment: bool = True) -> Dict[str, int]:
        """Get the current counter value.
        
        Args:
            increment: Whether to increment the counter after getting its value
            
        Returns:
            Dictionary containing the current counter value
        """
        current = self.counter
        if increment:
            self.counter += 1
            logger.debug("Counter incremented to %d", self.counter)
        return {"count": current}
    
    async def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Analyze a file and return basic information.
        
        This example shows how to work with files and handle errors.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary containing file metadata
            
        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If there are permission issues
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
            
        return {
            "path": str(path.absolute()),
            "size": path.stat().st_size,
            "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            "is_readable": os.access(path, os.R_OK),
            "is_writable": os.access(path, os.W_OK),
            "is_executable": os.access(path, os.X_OK)
        }

# Create a singleton instance
example_tools = ExampleTools()

# Export the tool functions
greet = example_tools.greet
create_task = example_tools.create_task
list_tasks = example_tools.list_tasks
get_counter = example_tools.get_counter
analyze_file = example_tools.analyze_file
