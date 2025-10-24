"""
Base Device Classes
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time


@dataclass
class DeviceParameter:
    """Device configuration parameter"""
    name: str
    value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = ""
    description: str = ""


class VirtualDevice(ABC):
    """Base class for all virtual devices"""
    
    def __init__(self, name: str, device_type: str):
        self.name = name
        self.device_type = device_type
        self.enabled = True
        self.last_update = 0.0
        
        # Device parameters (configurable in UI)
        self.parameters: Dict[str, DeviceParameter] = {}
        
        # Fault injection
        self.fault_enabled = False
        self.fault_type = ""
        self.fault_probability = 0.0
        
    @abstractmethod
    def update(self, sim_time: float, dt: float) -> None:
        """Update device state"""
        pass
        
    @abstractmethod
    def reset(self) -> None:
        """Reset device to initial state"""
        pass
        
    def set_parameter(self, name: str, value: Any) -> None:
        """Set device parameter"""
        if name in self.parameters:
            param = self.parameters[name]
            
            # Validate range
            if param.min_value is not None and value < param.min_value:
                value = param.min_value
            if param.max_value is not None and value > param.max_value:
                value = param.max_value
                
            param.value = value
            
    def get_parameter(self, name: str) -> Any:
        """Get device parameter value"""
        return self.parameters.get(name, DeviceParameter("", None)).value
        
    def inject_fault(self, fault_type: str, probability: float = 0.1) -> None:
        """Enable fault injection"""
        self.fault_enabled = True
        self.fault_type = fault_type
        self.fault_probability = probability
        
    def clear_fault(self) -> None:
        """Disable fault injection"""
        self.fault_enabled = False
        
    def _should_inject_fault(self) -> bool:
        """Check if fault should be injected this update"""
        if not self.fault_enabled:
            return False
        import random
        return random.random() < self.fault_probability