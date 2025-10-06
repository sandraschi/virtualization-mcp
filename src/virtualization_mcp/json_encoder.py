"""
Custom JSON encoder for handling VirtualBox objects and other non-serializable types.
"""
import json
import logging
import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Union, Set, TypeVar, Type, Callable

logger = logging.getLogger(__name__)

# Type variable for generic type hinting
T = TypeVar('T')

class VBoxJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles VirtualBox objects and other non-serializable types."""
    
    # Cache for type handlers to improve performance
    _type_handlers: Dict[Type, Callable[[Any], Any]] = {}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_type_handlers()
    
    def _setup_type_handlers(self):
        """Initialize type handlers for common VirtualBox types."""
        # Clear existing handlers
        self._type_handlers = {}
        
        # Try to import VirtualBox types
        try:
            from vboxapi import VirtualBoxManager  # type: ignore
            
            # Register VirtualBox type handlers
            vbox_manager = VirtualBoxManager(None, None)
            vbox = vbox_manager.getVirtualBox()
            
            # Common VirtualBox types
            vbox_types = [
                vbox_manager.constants.MachineState,
                vbox_manager.constants.DeviceType,
                vbox_manager.constants.StorageBus,
                vbox_manager.constants.NetworkAttachmentType,
                vbox_manager.constants.StorageControllerType,
                vbox_manager.constants.AudioDriverType,
                vbox_manager.constants.ChipsetType,
                vbox_manager.constants.DeviceType,
            ]
            
            # Register handlers for VirtualBox enum types
            for enum_type in vbox_types:
                if hasattr(enum_type, 'name'):
                    self._type_handlers[enum_type] = lambda x: x.name
            
            # Register handlers for VirtualBox objects
            self._type_handlers.update({
                vbox_manager.mgr.constants.MachineState: lambda x: x.name,
                vbox_manager.mgr.constants.SessionState: lambda x: x.name,
                vbox_manager.mgr.constants.SessionType: lambda x: x.name,
                vbox_manager.mgr.constants.LockType: lambda x: x.name,
            })
            
        except ImportError:
            logger.debug("VirtualBox Python bindings not available, using basic type handlers")
        
        # Register standard Python type handlers
        self._type_handlers.update({
            datetime: lambda x: x.isoformat(),
            set: list,
            frozenset: list,
            bytes: lambda x: x.decode('utf-8', errors='replace'),
            uuid.UUID: str,
            type(re.compile('')): lambda x: x.pattern,
            Enum: lambda x: x.name,
        })
    
    def default(self, obj: Any) -> Any:
        """Convert objects to a JSON-serializable format.
        
        Args:
            obj: The object to serialize
            
        Returns:
            A JSON-serializable version of the object
        """
        # Check for registered type handlers first
        for type_, handler in self._type_handlers.items():
            if isinstance(obj, type_) or (isinstance(type_, type) and isinstance(obj, type_)):
                try:
                    return handler(obj)
                except Exception as e:
                    logger.debug(f"Handler for {type_.__name__} failed: {e}")
                    break  # Fall through to default handling
        
        # Handle common non-serializable types
        if hasattr(obj, '__dict__'):
            # Convert objects with __dict__ to dict
            return self.clean_dict(obj.__dict__)
        elif hasattr(obj, '_asdict'):
            # Convert namedtuples to dict
            return self.clean_dict(obj._asdict())
        elif hasattr(obj, 'isoformat'):
            # Handle date/time objects
            return obj.isoformat()
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
            # Handle iterables (lists, sets, etc.)
            return [self.default(item) for item in obj]
        
        # Try to get a string representation as a fallback
        try:
            return str(obj)
        except Exception as e:
            logger.debug(f"Could not serialize object of type {type(obj).__name__}: {e}")
            return None
    
    def clean_dict(self, d: Any) -> Any:
        """Recursively clean a dictionary or object to ensure it's JSON-serializable.
        
        Args:
            d: Dictionary or object to clean
            
        Returns:
            Cleaned dictionary or value
        """
        if d is None:
            return None
            
        # Handle dictionaries
        if isinstance(d, dict):
            result = {}
            for key, value in d.items():
                # Skip private attributes
                if isinstance(key, str) and key.startswith('_'):
                    continue
                    
                try:
                    # Clean the value
                    cleaned_value = self.clean_dict(value)
                    
                    # Only include non-None values
                    if cleaned_value is not None:
                        result[key] = cleaned_value
                        
                except Exception as e:
                    logger.debug(f"Could not serialize {key}: {e}")
                    
            return result
            
        # Handle lists, tuples, and sets
        elif isinstance(d, (list, tuple, set)):
            result = []
            for item in d:
                try:
                    cleaned_item = self.clean_dict(item)
                    if cleaned_item is not None:
                        result.append(cleaned_item)
                except Exception as e:
                    logger.debug(f"Could not serialize list item: {e}")
            return result
            
        # Handle other objects with __dict__
        elif hasattr(d, '__dict__'):
            return self.clean_dict(d.__dict__)
            
        # Handle namedtuples
        elif hasattr(d, '_asdict'):
            return self.clean_dict(d._asdict())
            
        # Handle other types using the default encoder
        else:
            try:
                # Try to use the default encoder first
                return self.default(d)
            except Exception as e:
                logger.debug(f"Could not serialize value of type {type(d).__name__}: {e}")
                return str(d) if d is not None else None

def dumps(obj: Any, **kwargs) -> str:
    """Serialize obj to a JSON formatted str using the custom encoder."""
    return json.dumps(obj, cls=VBoxJSONEncoder, **kwargs)

def loads(json_str: str, **kwargs) -> Any:
    """Deserialize json_str to a Python object."""
    return json.loads(json_str, **kwargs)
