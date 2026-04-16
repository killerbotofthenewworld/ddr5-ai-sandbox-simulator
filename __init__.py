"""
DDR5 & DDR3 AI Sandbox Simulator

The Ultimate AI-Powered Memory Tuning Simulator Without Hardware Requirements
"""

__version__ = "7.0.0"
__author__ = "DDR5 AI Sandbox Simulator Team"
__license__ = "MIT"

from src import ddr5_models, ddr5_simulator, ai_optimizer
from src import ddr3_models, ddr3_simulator, ddr3_optimizer

__all__ = [
    "ddr5_models",
    "ddr5_simulator",
    "ai_optimizer",
    "ddr3_models",
    "ddr3_simulator",
    "ddr3_optimizer",
]
