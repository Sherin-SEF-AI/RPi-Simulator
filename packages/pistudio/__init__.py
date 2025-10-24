"""
PiStudio - Raspberry Pi Simulator

Main package providing CLI and programmatic interfaces.
"""

__version__ = "0.1.0"

from .simulator import PiSimulator
from .project import Project

__all__ = ["PiSimulator", "Project"]