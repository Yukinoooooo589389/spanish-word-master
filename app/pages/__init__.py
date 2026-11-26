"""页面集合。"""
from .dashboard import Dashboard
from .library import Library
from .quiz import Quiz
from .settings import Settings
from .stats import Stats
from .study import Study

__all__ = ["Dashboard", "Study", "Quiz", "Library", "Stats", "Settings"]