"""
网文创作专属工具集
基于 OpenHarness BaseTool 基类开发
"""

__version__ = "1.0.0"

from .character_validator import CharacterValidator
from .plot_coherence_checker import PlotCoherenceChecker
from .foreshadowing_detector import ForeshadowingDetector

__all__ = ["CharacterValidator", "PlotCoherenceChecker", "ForeshadowingDetector"]
