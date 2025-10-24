"""
Logic Analysis and Debugging Tools

Advanced tools for signal analysis, protocol decoding, and debugging.
"""

from .logic_analyzer import LogicAnalyzer, ChannelConfig
from .protocol_decoder import ProtocolDecoder, I2CDecoder, SPIDecoder, UARTDecoder
from .oscilloscope import VirtualOscilloscope
from .signal_generator import SignalGenerator

__all__ = [
    "LogicAnalyzer",
    "ChannelConfig", 
    "ProtocolDecoder",
    "I2CDecoder",
    "SPIDecoder", 
    "UARTDecoder",
    "VirtualOscilloscope",
    "SignalGenerator"
]