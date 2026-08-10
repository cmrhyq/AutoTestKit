from enum import Enum

from attr import dataclass


@dataclass
class MenuName(str, Enum):
    """
    首页/沙箱/AI可观测
    """
    INDEX = "index"
    SANDBOX = "sandbox"
    OBSERVABLE = "observable"